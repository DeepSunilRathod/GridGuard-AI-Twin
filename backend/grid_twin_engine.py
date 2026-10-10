"""Software-only GridGuard substation digital twin powered by pandapower.

All outputs are simulated. Demo thresholds are not protection settings.
"""
from datetime import datetime, timezone
import math
import random
import pandapower as pp

ASSETS = ("TX-01", "TX-02", "TX-03")
SCENARIOS = {"none", "overload", "overheating", "voltage_sag", "vibration"}
DEMO_LIMITS = {
    "transformer_loading_warning_percent": 80.0,
    "transformer_loading_critical_percent": 100.0,
    "voltage_warning_low_pu": 0.95,
    "voltage_warning_high_pu": 1.05,
    "temperature_warning_C": 65.0,
    "temperature_critical_C": 80.0,
    "vibration_warning_mm_s": 3.0,
    "vibration_critical_mm_s": 5.0,
}


class GridTwin:
    """Illustrative 110/11/0.4 kV network and condition signal models."""
    def __init__(self):
        self.rng = random.Random(42)
        self.scenarios = {a: "none" for a in ASSETS}
        self.breaker_closed = {a: True for a in ASSETS}
        # Existing backend's load_factor 0.75 maps to the nominal model demand.
        self.load_factor = {a: 0.75 for a in ASSETS}
        self.temperature = {a: 49.0 for a in ASSETS}
        self.vibration = {a: 1.6 for a in ASSETS}
        self.net, self.elements, self.lv_buses = self._build_network()

    def _build_network(self):
        net = pp.create_empty_network(sn_mva=10.0, f_hz=50.0)
        hv = pp.create_bus(net, vn_kv=110.0, name="GRID_110KV")
        mv = pp.create_bus(net, vn_kv=11.0, name="BUSBAR_11KV")
        pp.create_ext_grid(net, bus=hv, vm_pu=1.0, name="Utility grid")
        pp.create_transformer_from_parameters(
            net, hv_bus=hv, lv_bus=mv, sn_mva=10.0,
            vn_hv_kv=110.0, vn_lv_kv=11.0, vk_percent=10.0,
            vkr_percent=0.5, pfe_kw=12.0, i0_percent=0.1,
            shift_degree=0.0, name="MAIN-TX")
        elements, lv_buses = {}, {}
        for asset in ASSETS:
            lv = pp.create_bus(net, vn_kv=0.4, name=f"{asset}_LV")
            trafo = pp.create_transformer_from_parameters(
                net, hv_bus=mv, lv_bus=lv, sn_mva=0.4,
                vn_hv_kv=11.0, vn_lv_kv=0.4, vk_percent=6.0,
                vkr_percent=1.0, pfe_kw=1.0, i0_percent=0.2,
                shift_degree=0.0, name=asset)
            load = pp.create_load(net, bus=lv, p_mw=0.20, q_mvar=0.07, name=f"{asset}_LOAD")
            elements[asset] = {"trafo": trafo, "load": load}
            lv_buses[asset] = lv
        return net, elements, lv_buses

    def set_controls(self, asset_id, load_factor=None, fault=None, breaker_closed=None):
        self._check_asset(asset_id)
        if load_factor is not None:
            load_factor = float(load_factor)
            if not 0.1 <= load_factor <= 1.5:
                raise ValueError("load_factor must be between 0.1 and 1.5")
            self.load_factor[asset_id] = load_factor
        if fault is not None:
            fault = str(fault).strip().lower()
            if fault not in SCENARIOS:
                raise ValueError(f"fault must be one of {sorted(SCENARIOS)}")
            self.scenarios[asset_id] = fault
        if breaker_closed is not None:
            self.breaker_closed[asset_id] = bool(breaker_closed)
        return self.solve()

    def reset_asset(self, asset_id):
        self._check_asset(asset_id)
        self.scenarios[asset_id] = "none"
        self.breaker_closed[asset_id] = True
        self.load_factor[asset_id] = 0.75
        self.temperature[asset_id] = 49.0
        self.vibration[asset_id] = 1.6
        return self.solve()

    def reset(self):
        for asset in ASSETS:
            self.reset_asset(asset)
        return self.solve()

    def _prepare_network(self):
        for asset in ASSETS:
            ids = self.elements[asset]
            self.net.trafo.at[ids["trafo"], "in_service"] = self.breaker_closed[asset]
            # load_factor 0.75 is the nominal 0.20 MW / 0.07 MVAr demand.
            multiplier = self.load_factor[asset] / 0.75
            if self.scenarios[asset] == "overload":
                multiplier *= 1.5
            self.net.load.at[ids["load"], "p_mw"] = 0.20 * multiplier
            self.net.load.at[ids["load"], "q_mvar"] = 0.07 * multiplier
        # This starter models source-side voltage sag as a system-wide event.
        self.net.ext_grid.at[0, "vm_pu"] = 0.92 if "voltage_sag" in self.scenarios.values() else 1.0

    def solve(self):
        self._prepare_network()
        try:
            pp.runpp(self.net, calculate_voltage_angles=True, init="auto")
            converged, solve_error = bool(self.net.converged), None
        except Exception as exc:
            converged, solve_error = False, str(exc)
        now = datetime.now(timezone.utc).isoformat()
        results = {}
        for asset in ASSETS:
            ids = self.elements[asset]
            scenario = self.scenarios[asset]
            closed = self.breaker_closed[asset]
            bus_v = current = loading = power = None
            if converged and closed:
                try:
                    bus_v = float(self.net.res_bus.at[self.lv_buses[asset], "vm_pu"]) * 0.4
                    loading = float(self.net.res_trafo.at[ids["trafo"], "loading_percent"])
                    current = float(self.net.res_trafo.at[ids["trafo"], "i_lv_ka"]) * 1000.0
                    power = float(self.net.res_load.at[ids["load"], "p_mw"])
                    if not all(math.isfinite(v) for v in (bus_v, loading, current, power)):
                        bus_v = current = loading = power = None
                except (ValueError, TypeError, KeyError):
                    bus_v = current = loading = power = None
            # Simple thermal and vibration response models for the virtual asset.
            if closed and loading is not None:
                target_temp = 30.0 + 0.45 * loading + (25.0 if scenario == "overheating" else 0.0)
                target_vib = 5.5 if scenario == "vibration" else 1.0 + 0.015 * max(0.0, loading)
                self.temperature[asset] += 0.18 * (target_temp - self.temperature[asset])
                self.vibration[asset] += 0.25 * (target_vib - self.vibration[asset])
            else:
                self.temperature[asset] += 0.10 * (30.0 - self.temperature[asset])
                self.vibration[asset] += 0.20 * (0.4 - self.vibration[asset])
            temp = max(20.0, self.temperature[asset] + self.rng.uniform(-0.15, 0.15))
            vib = max(0.0, self.vibration[asset] + self.rng.uniform(-0.03, 0.03))
            reasons = []
            if not closed:
                status = "out_of_service"
                reasons.append("Feeder breaker is open")
            elif not converged or loading is None:
                status = "simulation_error"
                reasons.append("Power-flow result unavailable; inspect network state")
            else:
                if scenario != "none":
                    reasons.append(f"Injected scenario: {scenario}")
                if loading >= DEMO_LIMITS["transformer_loading_critical_percent"]:
                    reasons.append("Transformer loading at or above 100% demo threshold")
                elif loading >= DEMO_LIMITS["transformer_loading_warning_percent"]:
                    reasons.append("Transformer loading above demo warning threshold")
                if temp >= DEMO_LIMITS["temperature_critical_C"]:
                    reasons.append("Temperature above demo critical threshold")
                elif temp >= DEMO_LIMITS["temperature_warning_C"]:
                    reasons.append("Temperature above demo warning threshold")
                if vib >= DEMO_LIMITS["vibration_critical_mm_s"]:
                    reasons.append("Vibration above demo critical threshold")
                elif vib >= DEMO_LIMITS["vibration_warning_mm_s"]:
                    reasons.append("Vibration above demo warning threshold")
                if bus_v is not None and not (0.38 <= bus_v <= 0.42):
                    reasons.append("LV bus voltage outside illustrative 0.38–0.42 kV band")
                if (scenario == "overheating" or temp >= 80.0 or vib >= 5.0 or (loading is not None and loading >= 100.0)):
                    status = "critical"
                elif scenario != "none" or temp >= 65.0 or vib >= 3.0 or (loading is not None and loading >= 80.0) or (bus_v is not None and not 0.38 <= bus_v <= 0.42):
                    status = "warning"
                else:
                    status = "normal"
            results[asset] = {
                "asset_id": asset,
                "timestamp": now,
                "current_A": round(current, 3) if current is not None else 0.0,
                "voltage_kV": round(bus_v, 4) if bus_v is not None else 0.0,
                "temperature_C": round(temp, 2),
                "vibration_mm_s": round(vib, 3),
                "load_factor": round(self.load_factor[asset], 2),
                "fault_scenario": scenario,
                "breaker_closed": closed,
                "transformer_loading_percent": round(loading, 2) if loading is not None else None,
                "real_power_MW": round(power, 5) if power is not None else None,
                "status": status,
                "status_reasons": reasons,
                "demo_rul_hours": None,
                "rul_is_demo": True,
                "data_source": "software_digital_twin_pandapower",
                "simulated_data": True,
                "power_flow_converged": bool(converged),
            }
        return {
            "timestamp": now,
            "data_source": "software_digital_twin_pandapower",
            "simulation_type": "pandapower steady-state prototype + illustrative condition models",
            "simulated_data": True,
            "converged": bool(converged),
            "solve_error": solve_error,
            "assets": results,
            "demo_limits": DEMO_LIMITS,
        }

    @staticmethod
    def _check_asset(asset_id):
        if asset_id not in ASSETS:
            raise ValueError(f"Unknown asset_id. Choose one of {ASSETS}")

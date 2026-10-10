```javascript
export function runAsync(callback) {
  return setTimeout(() => {
    Promise.resolve(callback()).catch((error) => {
      console.error("Refresh failed:", error);
    });
  }, 0);
}

export function startRefreshInterval(callback, interval = 3000) {
  const initial = runAsync(callback);

  const intervalId = setInterval(() => {
    Promise.resolve(callback()).catch((error) => {
      console.error("Refresh failed:", error);
    });
  }, interval);

  return () => {
    clearTimeout(initial);
    clearInterval(intervalId);
  };
}
```
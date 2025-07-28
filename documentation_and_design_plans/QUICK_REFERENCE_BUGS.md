# Quick Reference: Common React Bugs & Fixes

## 🚨 Bug #1: "Objects are not valid as a React child"

### **Symptoms:**
- Blank page when clicking buttons
- Error in console: `Objects are not valid as a React child (found: object with keys {...})`
- Component crashes when trying to render API response

### **Root Cause:**
Trying to render JavaScript objects directly in React components.

### **Example of Broken Code:**
```typescript
// ❌ WRONG - API returns object, trying to render it directly
setGeneratedConfig(response.data.config);
```

### **Fix:**
Format objects into strings before rendering:
```typescript
// ✅ CORRECT - Format object for display
const configData = response.data.config;
let formattedConfig = "";

if (typeof configData === 'object' && configData !== null) {
  Object.entries(configData).forEach(([device, configs]) => {
    formattedConfig += `=== ${device} ===\n`;
    if (Array.isArray(configs)) {
      configs.forEach(config => {
        formattedConfig += `${config}\n`;
      });
    }
    formattedConfig += '\n';
  });
} else if (typeof configData === 'string') {
  formattedConfig = configData;
} else {
  formattedConfig = "Configuration generated successfully";
}

setGeneratedConfig(formattedConfig);
```

---

## 🚨 Bug #2: useState Inside Render Function

### **Symptoms:**
- Blank page after component loads
- Error: `Invalid hook call`
- Component shows briefly then disappears

### **Root Cause:**
React hooks placed inside render functions or IIFEs.

### **Example of Broken Code:**
```typescript
// ❌ WRONG - useState inside render function
export default function Component() {
  return (
    <div>
      {(() => {
        const [state, setState] = useState(false); // This breaks React!
        return <div>...</div>;
      })()}
    </div>
  );
}
```

### **Fix:**
Move hooks to component top level:
```typescript
// ✅ CORRECT - useState at component level
export default function Component() {
  const [state, setState] = useState(false);
  
  return (
    <div>
      {/* Use state here */}
    </div>
  );
}
```

---

## 🚨 Bug #3: Theme Hook Import Errors

### **Symptoms:**
- Error: `Failed to resolve import "@/hooks/use-theme"`
- React app crashes on load
- Blank page with import errors

### **Root Cause:**
Missing theme hook file or incorrect imports.

### **Fix:**
1. Remove theme hook imports temporarily:
```typescript
// Remove these lines
// import { useTheme } from "@/hooks/use-theme";
// const { theme, toggleTheme } = useTheme();
```

2. Or create the missing theme hook file:
```typescript
// frontend/src/hooks/use-theme.ts
import { useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark');
    }
  }, []);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return { theme, toggleTheme };
}
```

---

## 🔧 Debugging Tools We Added

### **1. Global Error Handlers**
```typescript
// frontend/src/main.tsx
window.addEventListener('error', function (event) {
  console.error('🚨 Global error caught:', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error,
    stack: event.error?.stack
  });
});

window.addEventListener('unhandledrejection', function (event) {
  console.error('🚨 Unhandled promise rejection:', {
    reason: event.reason,
    stack: event.reason?.stack
  });
});
```

### **2. React Error Boundary**
```typescript
// frontend/src/components/ErrorBoundary.tsx
export class ErrorBoundary extends Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('🚨 ErrorBoundary caught an error:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    });
  }
  
  // ... rest of implementation
}
```

### **3. Enhanced Logging**
```typescript
// Add to components for debugging
const addDebugLog = (message: string) => {
  const timestamp = new Date().toLocaleTimeString();
  const logMessage = `[${timestamp}] ${message}`;
  console.log(`🔍 Debug: ${message}`);
  setDebugLogs(prev => [...prev, logMessage]);
};
```

---

## 📋 Quick Checklist

When encountering blank pages or crashes:

1. **Check Console Errors** - Look for specific error messages
2. **Verify Hook Placement** - Ensure hooks are at component top level
3. **Check Object Rendering** - Format objects before displaying
4. **Clear Vite Cache** - Run `rm -rf node_modules/.vite && npm run dev`
5. **Use Error Boundary** - Wrap components to catch render errors
6. **Add Debug Logging** - Log each step to identify where it fails

---

*Last Updated: July 28, 2025*  
*Status: ✅ All bugs documented and fixes implemented* 
# React Hooks Troubleshooting Guide

## 🚨 Common Issue: useState Inside Render Function

### **Problem Description**
When React components fail to load or show blank pages, one of the most common causes is **React Hooks Rules violations**. This document covers the specific issue we encountered and how to fix it.

### **❌ What Broke Our Application**

**Issue**: Bridge Builder page (`http://localhost:8080/builder`) showed blank page after loading for a split second.

**Root Cause**: `useState` hook was placed inside the render function, violating React Hooks Rules.

```typescript
// ❌ WRONG - useState inside render function
export default function BridgeBuilder() {
  return (
    <div>
      {(() => {
        const [expandedGroups, setExpandedGroups] = useState({...}); // This breaks React!
        return <div>...</div>;
      })()}
    </div>
  );
}
```

### **✅ Correct Fix**

**Solution**: Move all hooks to the component's top level.

```typescript
// ✅ CORRECT - useState at component level
export default function BridgeBuilder() {
  const [expandedGroups, setExpandedGroups] = useState({
    superspine: false,
    spine: false,
    leaf: false,
    unknown: false
  });
  
  const toggleGroup = (group: string) => {
    setExpandedGroups(prev => ({...prev, [group]: !prev[group]}));
  };

  return (
    <div>
      {/* Use the state here */}
    </div>
  );
}
```

## 🚨 Additional Issue: IIFE in Render Function

### **Problem Description**
Another common cause of blank pages is using **IIFE (Immediately Invoked Function Expression)** inside render functions, even without hooks.

### **❌ What Broke Our Application (Second Issue)**

**Issue**: Bridge Builder page showed blank page when clicking "Generate" button.

**Root Cause**: IIFE inside render function was causing React to think there might be hooks.

```typescript
// ❌ WRONG - IIFE inside render function
return (
  <div>
    {(() => {
      const groupedDevices = groupDevicesByType(devices);
      return <div>...</div>;
    })()}
  </div>
);
```

### **✅ Correct Fix for IIFE Issue**

**Solution**: Extract the logic into a separate component or move it outside the render.

```typescript
// ✅ CORRECT - Separate component
const DeviceTopologyRenderer = ({ devices, ...props }) => {
  const groupedDevices = groupDevicesByType(devices);
  return <div>...</div>;
};

// ✅ CORRECT - Use the component
return (
  <div>
    <DeviceTopologyRenderer devices={devices} {...props} />
  </div>
);
```

## 🚨 Critical Issue: "Objects are not valid as a React child"

### **Problem Description**
This is a **critical rendering error** that occurs when trying to render JavaScript objects directly in React components.

### **❌ What Broke Our Application (Third Issue)**

**Issue**: Bridge Builder page showed blank page when clicking "Generate Configuration" button.

**Error Message**:
```
Objects are not valid as a React child (found: object with keys {DNAAS-LEAF-B02, DNAAS-LEAF-B05, DNAAS-SPINE-B08}). If you meant to render a collection of children, use an array instead.
```

**Root Cause**: The API was returning a configuration object like this:
```javascript
{
  'DNAAS-LEAF-B05': ['config line 1', 'config line 2'],
  'DNAAS-SPINE-B08': ['config line 1', 'config line 2'],
  'DNAAS-LEAF-B02': ['config line 1', 'config line 2']
}
```

But the React component was trying to render this object directly as text:
```typescript
// ❌ WRONG - Trying to render object directly
setGeneratedConfig(response.data.config || "Configuration generated successfully");
```

### **✅ Correct Fix for Object Rendering Issue**

**Solution**: Format the object into a readable string before rendering.

```typescript
// ✅ CORRECT - Format object for display
const configData = response.data.config;
let formattedConfig = "";

if (typeof configData === 'object' && configData !== null) {
  // If it's an object with device configurations
  Object.entries(configData).forEach(([device, configs]) => {
    formattedConfig += `=== ${device} ===\n`;
    if (Array.isArray(configs)) {
      configs.forEach(config => {
        formattedConfig += `${config}\n`;
      });
    } else {
      formattedConfig += `${configs}\n`;
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

**Result**: The configuration is now properly formatted as:
```
=== DNAAS-LEAF-B05 ===
config line 1
config line 2

=== DNAAS-SPINE-B08 ===
config line 1
config line 2

=== DNAAS-LEAF-B02 ===
config line 1
config line 2
```

## 🌙 Dark Mode Issues: Why It Keeps Breaking

### **Problem Description**
Dark mode functionality keeps causing React app crashes due to **SSR (Server-Side Rendering)** issues and **path resolution problems**.

### **❌ Common Dark Mode Issues**

1. **SSR Window Access**: Trying to access `window` during server-side rendering
2. **Path Resolution**: TypeScript can't resolve `@/hooks/use-theme` import
3. **Initialization Timing**: Theme hook trying to access localStorage before DOM is ready

### **✅ Fixed Dark Mode Implementation**

**Solution**: Simplified theme hook that avoids SSR issues:

```typescript
// ✅ CORRECT - Simple theme hook
export function useTheme() {
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    // Initialize theme from localStorage or system preference
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

### **🔧 Dark Mode Troubleshooting Steps**

1. **Check Import Path**: Ensure `@/hooks/use-theme` resolves correctly
2. **Avoid SSR Issues**: Don't access `window` in initial state
3. **Use useEffect**: Initialize theme after component mounts
4. **Test Incrementally**: Add theme functionality step by step

### **🚨 Dark Mode Error Messages**

- `"Failed to resolve import "@/hooks/use-theme"`
- `"Cannot read property 'localStorage' of undefined"`
- `"window is not defined"`
- `"Invalid hook call"`

### **💡 Dark Mode Best Practices**

1. **Always use useEffect** for browser-only operations
2. **Provide fallback values** for initial state
3. **Test theme switching** in development
4. **Keep theme logic simple** and avoid complex SSR handling

## 📋 React Hooks Rules Checklist

### **✅ Always Do This:**
1. **Call hooks at the top level** of your component
2. **Call hooks in the same order** every render
3. **Only call hooks from React components** or custom hooks
4. **Use hooks before any early returns**

### **❌ Never Do This:**
1. **Don't call hooks inside loops**
2. **Don't call hooks inside conditions**
3. **Don't call hooks inside nested functions**
4. **Don't call hooks inside render functions**
5. **Don't call hooks inside callbacks**

## 🔧 Quick Debugging Steps

### **Step 1: Check for Hook Violations**
Look for these patterns in your code:
- `useState` inside `map()` functions
- `useState` inside `if` statements
- `useState` inside IIFEs (Immediately Invoked Function Expressions)
- `useState` inside render callbacks

### **Step 2: Move Hooks to Top Level**
```typescript
// Before (broken)
function MyComponent() {
  return (
    <div>
      {items.map(item => {
        const [state, setState] = useState(false); // ❌ Wrong!
        return <div>{item}</div>;
      })}
    </div>
  );
}

// After (fixed)
function MyComponent() {
  const [states, setStates] = useState({}); // ✅ Correct!
  
  return (
    <div>
      {items.map(item => (
        <div key={item.id}>{item}</div>
      ))}
    </div>
  );
}
```

### **Step 3: Use Custom Hooks for Complex Logic**
```typescript
// ✅ Good practice
function useDeviceGrouping(devices) {
  const [expandedGroups, setExpandedGroups] = useState({});
  
  const toggleGroup = useCallback((group) => {
    setExpandedGroups(prev => ({...prev, [group]: !prev[group]}));
  }, []);
  
  return { expandedGroups, toggleGroup };
}
```

## 🚨 Error Messages to Watch For

### **Common Error Messages:**
- `"React Hook "useState" is called conditionally"`
- `"React Hook "useState" is called in a loop"`
- `"React Hook "useState" is called inside a callback"`
- `"Invalid hook call"`
- `"Objects are not valid as a React child"`

### **Browser Console Errors:**
- `Uncaught Error: Invalid hook call`
- `React has detected a change in the order of Hooks`
- `Rendered fewer hooks than expected`

## 🛠️ Prevention Strategies

### **1. ESLint Rules**
Add these ESLint rules to catch hook violations:
```json
{
  "rules": {
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

### **2. Code Review Checklist**
- [ ] All hooks called at component top level
- [ ] No hooks inside loops or conditions
- [ ] No hooks inside nested functions
- [ ] Custom hooks follow naming convention (`use` prefix)
- [ ] Objects are properly formatted before rendering

### **3. Testing Strategy**
- Test component rendering after state changes
- Verify hooks are called in consistent order
- Check for memory leaks with cleanup functions

## 📚 Related Resources

- [React Hooks Rules](https://react.dev/warnings/invalid-hook-call-warning)
- [React Hooks FAQ](https://react.dev/reference/react/hooks#rules-of-hooks)
- [Custom Hooks Guide](https://react.dev/learn/reusing-logic-with-custom-hooks)

## 🎯 Summary

**The key takeaway**: Always place React hooks at the top level of your component, never inside render functions, loops, or conditions. This ensures React can maintain the correct hook order across renders.

**When in doubt**: If you need conditional logic with hooks, use the hook first, then conditionally update the state or use conditional rendering.

---

*Last Updated: July 28, 2025*  
*Issue: Bridge Builder page blank due to useState in render function*  
*Status: ✅ Fixed by moving hooks to component top level*  
*Additional Issue: Objects not valid as React child*  
*Status: ✅ Fixed by properly formatting objects for display* 
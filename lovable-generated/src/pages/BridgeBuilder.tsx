import { useState } from "react";
import { CheckCircle, Circle, Router, Network, Settings, Eye, Plus, Trash2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

const steps = [
  { id: 1, title: "Service Configuration", icon: Settings },
  { id: 2, title: "Source Selection", icon: Network },
  { id: 3, title: "Destination Setup", icon: Router },
  { id: 4, title: "Review & Generate", icon: Eye }
];

// Real device data organized by rows as shown in CLI
const devicesByRow = {
  "A": [
    "DNAAS-LEAF-A10", "DNAAS-LEAF-A11-1", "DNAAS-LEAF-A11-2", "DNAAS-LEAF-A12",
    "DNAAS-LEAF-A13", "DNAAS-LEAF-A14", "DNAAS-LEAF-A15", "DNAAS-LEAF-A16"
  ],
  "B": [
    "DNAAS-LEAF-B01", "DNAAS-LEAF-B02", "DNAAS-LEAF-B03", "DNAAS-LEAF-B04",
    "DNAAS-LEAF-B05", "DNAAS-LEAF-B06-1", "DNAAS-LEAF-B06-2-(NCPL)", "DNAAS-LEAF-B07",
    "DNAAS-LEAF-B10", "DNAAS-LEAF-B13", "DNAAS-LEAF-B14", "DNAAS-LEAF-B15", "DNAAS-LEAF-B16"
  ],
  "C": [
    "DNAAS-LEAF-C10", "DNAAS-LEAF-C11", "DNAAS-LEAF-C12-A", "DNAAS-LEAF-C13",
    "DNAAS-LEAF-C15", "DNAAS-LEAF-C16"
  ],
  "D": [
    "DNAAS-SUPERSPINE-D04", "DNAAS-LEAF-D12", "DNAAS-LEAF-D13", "DNAAS-LEAF-D16"
  ],
  "F": [
    "DNAAS-LEAF-F14", "DNAAS-LEAF-F15", "DNAAS-LEAF-F16"
  ]
};

// Generate interfaces like in CLI (ge100-0/0/1 through ge100-0/0/48)
const generateInterfaces = () => {
  const interfaces = [];
  for (let i = 1; i <= 48; i++) {
    interfaces.push(`ge100-0/0/${i}`);
  }
  return interfaces;
};

const getDeviceType = (deviceName: string) => {
  if (deviceName.includes("SUPERSPINE")) return "superspine";
  if (deviceName.includes("SPINE")) return "spine";
  if (deviceName.includes("LEAF")) return "leaf";
  return "unknown";
};

const getDeviceIcon = (type: string) => {
  switch (type) {
    case "superspine": return "🌲";
    case "spine": return "🌳"; 
    case "leaf": return "🌿";
    default: return "🔧";
  }
};

interface Destination {
  device: string;
  interfaceName: string;
}

export default function BridgeBuilder() {
  const [currentStep, setCurrentStep] = useState(1);
  const [username, setUsername] = useState("");
  const [vlanId, setVlanId] = useState("");
  const [sourceDevice, setSourceDevice] = useState("");
  const [sourceInterface, setSourceInterface] = useState("");
  const [destinations, setDestinations] = useState<Destination[]>([]);
  const [currentDestDevice, setCurrentDestDevice] = useState("");
  const [currentDestInterface, setCurrentDestInterface] = useState("");
  const [showAddDestination, setShowAddDestination] = useState(false);

  const serviceName = username && vlanId ? `g_${username}_v${vlanId}` : "";
  const interfaces = generateInterfaces();

  const isStepComplete = (stepId: number) => {
    switch (stepId) {
      case 1: return username !== "" && vlanId !== "";
      case 2: return sourceDevice !== "" && sourceInterface !== "";
      case 3: return destinations.length > 0;
      case 4: return true; // Review step is always complete if reached
      default: return false;
    }
  };

  const canProceed = isStepComplete(currentStep);

  const handleNext = () => {
    if (canProceed && currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const addDestination = () => {
    if (currentDestDevice && currentDestInterface) {
      setDestinations([...destinations, { 
        device: currentDestDevice, 
        interfaceName: currentDestInterface 
      }]);
      setCurrentDestDevice("");
      setCurrentDestInterface("");
      setShowAddDestination(false);
    }
  };

  const removeDestination = (index: number) => {
    setDestinations(destinations.filter((_, i) => i !== index));
  };

  // Flatten all devices for dropdown
  const allDevices = Object.entries(devicesByRow).flatMap(([row, devices]) => 
    devices.map(device => ({ name: device, row, type: getDeviceType(device) }))
  );

  // Filter out already selected devices
  const availableDevices = allDevices.filter(device => 
    device.name !== sourceDevice && 
    !destinations.some(dest => dest.device === device.name)
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Unified Bridge Domain Builder</h1>
        <p className="text-muted-foreground mt-2">
          Create P2P & P2MP bridge domain configurations with guided setup
        </p>
      </div>

      {/* Progress Steps */}
      <Card className="shadow-card">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                    currentStep === step.id 
                      ? "bg-primary border-primary text-primary-foreground" 
                      : isStepComplete(step.id)
                      ? "bg-success border-success text-success-foreground"
                      : "border-muted-foreground text-muted-foreground"
                  }`}>
                    {isStepComplete(step.id) && currentStep !== step.id ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <step.icon className="w-5 h-5" />
                    )}
                  </div>
                  <div className="ml-3 hidden md:block">
                    <div className={`text-sm font-medium ${
                      currentStep === step.id ? "text-primary" : 
                      isStepComplete(step.id) ? "text-success" : "text-muted-foreground"
                    }`}>
                      {step.title}
                    </div>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className={`w-12 h-0.5 mx-4 ${
                    isStepComplete(step.id) ? "bg-success" : "bg-muted"
                  }`} />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>{steps[currentStep - 1].title}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Step 1: Service Configuration */}
              {currentStep === 1 && (
                <div className="space-y-6">
                  <div className="space-y-4">
                    <Label htmlFor="username">Username (e.g., visaev)</Label>
                    <Input
                      id="username"
                      placeholder="Enter your username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                    />
                  </div>
                  <div className="space-y-4">
                    <Label htmlFor="vlan">VLAN ID (e.g., 253)</Label>
                    <Input
                      id="vlan"
                      placeholder="Enter VLAN ID"
                      value={vlanId}
                      onChange={(e) => setVlanId(e.target.value)}
                    />
                  </div>
                  {serviceName && (
                    <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
                      <div className="text-sm font-medium text-primary">Service name will be:</div>
                      <div className="text-lg font-mono font-bold text-primary mt-1">
                        {serviceName}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Step 2: Source Selection */}
              {currentStep === 2 && (
                <div className="space-y-6">
                  <div className="space-y-4">
                    <Label>Source Device Selection</Label>
                    <Select value={sourceDevice} onValueChange={setSourceDevice}>
                      <SelectTrigger className="bg-background">
                        <SelectValue placeholder="Select source device (row-rack format)" />
                      </SelectTrigger>
                      <SelectContent className="bg-background border shadow-elevated">
                        {Object.entries(devicesByRow).map(([row, devices]) => (
                          <div key={row} className="p-2">
                            <div className="text-xs font-semibold text-muted-foreground mb-2">
                              🏢 Row {row}:
                            </div>
                            {devices.map((device) => (
                              <SelectItem key={device} value={device} className="pl-4">
                                <div className="flex items-center gap-2">
                                  <span>{getDeviceIcon(getDeviceType(device))}</span>
                                  <span className="font-mono text-sm">{device}</span>
                                </div>
                              </SelectItem>
                            ))}
                          </div>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {sourceDevice && (
                    <div className="space-y-4">
                      <Label>Source Interface Selection</Label>
                      <Select value={sourceInterface} onValueChange={setSourceInterface}>
                        <SelectTrigger className="bg-background">
                          <SelectValue placeholder="Select source interface" />
                        </SelectTrigger>
                        <SelectContent className="bg-background border shadow-elevated max-h-60">
                           {interfaces.map((interfaceName, index) => (
                             <SelectItem key={interfaceName} value={interfaceName}>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">
                                  {index + 1}.
                                </span>
                                 <span className="font-mono">{interfaceName}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {sourceInterface && (
                        <div className="p-4 bg-success/5 border border-success/20 rounded-lg">
                          <div className="text-sm font-medium text-success">
                            ✅ Selected: {sourceDevice}:{sourceInterface}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Step 3: Destination Setup */}
              {currentStep === 3 && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <Label>Destination Configuration</Label>
                    <Button
                      onClick={() => setShowAddDestination(true)}
                      className="flex items-center gap-2"
                      size="sm"
                    >
                      <Plus className="w-4 h-4" />
                      Add Destination
                    </Button>
                  </div>

                  {/* Current Destinations */}
                  <div className="space-y-3">
                    <div className="text-sm font-medium">
                      📋 Current destinations: {destinations.length}
                    </div>
                    {destinations.map((dest, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border">
                        <div>
                          <div className="font-medium font-mono">{dest.device}</div>
                          <div className="text-sm text-muted-foreground font-mono">
                            Interface: {dest.interfaceName}
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeDestination(index)}
                          className="text-destructive hover:text-destructive-foreground hover:bg-destructive"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>

                  {/* Add Destination Form */}
                  {showAddDestination && (
                    <Card className="border-primary/20 bg-primary/5">
                      <CardContent className="p-4 space-y-4">
                        <div className="space-y-3">
                          <Label>Select Destination Device</Label>
                          <Select value={currentDestDevice} onValueChange={setCurrentDestDevice}>
                            <SelectTrigger className="bg-background">
                              <SelectValue placeholder="Choose destination device" />
                            </SelectTrigger>
                            <SelectContent className="bg-background border shadow-elevated">
                              {Object.entries(devicesByRow).map(([row, devices]) => (
                                <div key={row} className="p-2">
                                  <div className="text-xs font-semibold text-muted-foreground mb-2">
                                    🏢 Row {row}:
                                  </div>
                                  {devices
                                    .filter(device => device !== sourceDevice && 
                                      !destinations.some(dest => dest.device === device))
                                    .map((device) => (
                                    <SelectItem key={device} value={device} className="pl-4">
                                      <div className="flex items-center gap-2">
                                        <span>{getDeviceIcon(getDeviceType(device))}</span>
                                        <span className="font-mono text-sm">{device}</span>
                                      </div>
                                    </SelectItem>
                                  ))}
                                </div>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {currentDestDevice && (
                          <div className="space-y-3">
                            <Label>Destination Interface</Label>
                            <Select value={currentDestInterface} onValueChange={setCurrentDestInterface}>
                              <SelectTrigger className="bg-background">
                                <SelectValue placeholder="Select destination interface" />
                              </SelectTrigger>
                              <SelectContent className="bg-background border shadow-elevated max-h-60">
                                 {interfaces.map((interfaceName, index) => (
                                   <SelectItem key={interfaceName} value={interfaceName}>
                                     <div className="flex items-center gap-2">
                                       <span className="text-xs text-muted-foreground">
                                         {index + 1}.
                                       </span>
                                       <span className="font-mono">{interfaceName}</span>
                                    </div>
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button 
                            onClick={addDestination}
                            disabled={!currentDestDevice || !currentDestInterface}
                            size="sm"
                          >
                            Add Destination
                          </Button>
                          <Button 
                            variant="outline" 
                            onClick={() => {
                              setShowAddDestination(false);
                              setCurrentDestDevice("");
                              setCurrentDestInterface("");
                            }}
                            size="sm"
                          >
                            Cancel
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {destinations.length > 0 && (
                    <div className="p-4 bg-network-accent/5 border border-network-accent/20 rounded-lg">
                      <div className="text-sm font-medium text-network-accent">
                        💡 Configuration type: {destinations.length === 1 ? "P2P" : "P2MP"} 
                        ({destinations.length} destination{destinations.length > 1 ? "s" : ""})
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Step 4: Review & Generate */}
              {currentStep === 4 && (
                <div className="space-y-6">
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">📋 Unified Configuration Summary</h3>
                    <Separator />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Service Name:</span>
                          <span className="font-mono font-medium">{serviceName}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">VLAN ID:</span>
                          <span className="font-mono font-medium">{vlanId}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Topology Type:</span>
                          <Badge variant="outline">
                            {destinations.length === 1 ? "P2P" : "P2MP"}
                          </Badge>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Source Device:</span>
                          <span className="font-mono font-medium">{sourceDevice}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Source Interface:</span>
                          <span className="font-mono font-medium">{sourceInterface}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Devices Configured:</span>
                          <span className="font-medium">{destinations.length + 1}</span>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div className="space-y-3">
                      <h4 className="font-medium">Destination Details:</h4>
                      {destinations.map((dest, index) => (
                        <div key={index} className="flex justify-between items-center p-3 bg-muted/30 rounded-lg">
                          <div>
                            <div className="font-medium font-mono">{dest.device}</div>
                            <div className="text-sm text-muted-foreground font-mono">
                              {dest.interfaceName}
                            </div>
                          </div>
                          <Badge variant="outline" className="bg-success/10 text-success">
                            {getDeviceIcon(getDeviceType(dest.device))} {getDeviceType(dest.device)}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Configuration Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {serviceName && (
                <div className="text-sm">
                  <div className="font-medium">Service Name:</div>
                  <div className="text-muted-foreground mt-1 font-mono">{serviceName}</div>
                </div>
              )}
              {sourceDevice && (
                <div className="text-sm">
                  <div className="font-medium">Source:</div>
                  <div className="text-muted-foreground mt-1 font-mono">
                    {sourceDevice}
                    {sourceInterface && `:${sourceInterface}`}
                  </div>
                </div>
              )}
              {destinations.length > 0 && (
                <div className="text-sm">
                  <div className="font-medium">Destinations:</div>
                  <div className="text-muted-foreground mt-1">
                    {destinations.length} device{destinations.length > 1 ? "s" : ""} configured
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Device Topology</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm">
                {Object.entries(devicesByRow).map(([row, devices]) => (
                  <div key={row}>
                    <div className="font-semibold text-muted-foreground mb-2">
                      🏢 Row {row}:
                    </div>
                    <div className="space-y-1 pl-4">
                      {devices.map((device) => (
                        <div key={device} className="flex items-center gap-2">
                          <span>{getDeviceIcon(getDeviceType(device))}</span>
                          <span className={`font-mono text-xs ${
                            device === sourceDevice ? "text-primary font-bold" :
                            destinations.some(d => d.device === device) ? "text-network-accent font-bold" :
                            "text-muted-foreground"
                          }`}>
                            {device}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Navigation */}
      <Card className="shadow-card">
        <CardContent className="p-6">
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 1}
            >
              Previous
            </Button>
            <div className="flex gap-2">
              {currentStep === 4 ? (
                <>
                  <Button variant="outline" disabled={!canProceed}>
                    Save to Pending
                  </Button>
                  <Button disabled={!canProceed}>
                    Generate & Deploy
                  </Button>
                </>
              ) : (
                <Button onClick={handleNext} disabled={!canProceed}>
                  Next
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
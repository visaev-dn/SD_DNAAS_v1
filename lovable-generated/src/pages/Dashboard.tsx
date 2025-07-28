import { Activity, Router, FileText, Network, TrendingUp, Clock, CheckCircle, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

const stats = [
  {
    title: "Total Devices",
    value: "147",
    change: "+12%",
    icon: Network,
    color: "text-network-primary"
  },
  {
    title: "Active Deployments", 
    value: "8",
    change: "+3",
    icon: Router,
    color: "text-primary"
  },
  {
    title: "Bridge Domains",
    value: "324",
    change: "+28",
    icon: Activity,
    color: "text-network-accent"
  },
  {
    title: "Configuration Files",
    value: "1,247",
    change: "+156",
    icon: FileText,
    color: "text-secondary"
  }
];

const recentActivity = [
  {
    action: "Bridge Domain Created",
    device: "spine-01",
    time: "2 minutes ago",
    status: "success"
  },
  {
    action: "Configuration Deployed",
    device: "leaf-23",
    time: "15 minutes ago", 
    status: "success"
  },
  {
    action: "Device Discovery",
    device: "superspine-02",
    time: "1 hour ago",
    status: "warning"
  },
  {
    action: "File Upload",
    device: "topology.yaml",
    time: "2 hours ago",
    status: "success"
  }
];

const activeDeployments = [
  {
    name: "P2P-VLAN-2001",
    progress: 85,
    devices: 4,
    status: "deploying"
  },
  {
    name: "P2MP-Service-Core",
    progress: 45,
    devices: 12,
    status: "deploying"
  },
  {
    name: "Leaf-Interconnect",
    progress: 100,
    devices: 8,
    status: "completed"
  }
];

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Lab Automation Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Network automation and configuration management platform
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title} className="shadow-card hover:shadow-elevated transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3 text-success" />
                  <span className="text-xs text-success font-medium">
                    {stat.change}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    from last week
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Quick Actions */}
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button size="lg" className="w-full justify-start h-12">
              <Router className="mr-3 h-5 w-5" />
              Create Bridge Domain
            </Button>
            <Button variant="outline" size="lg" className="w-full justify-start h-12">
              <FileText className="mr-3 h-5 w-5" />
              Upload Configuration
            </Button>
            <Button variant="outline" size="lg" className="w-full justify-start h-12">
              <Network className="mr-3 h-5 w-5" />
              Discover Devices
            </Button>
            <Button variant="outline" size="lg" className="w-full justify-start h-12">
              <Activity className="mr-3 h-5 w-5" />
              View Topology
            </Button>
          </CardContent>
        </Card>

        {/* Active Deployments */}
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Active Deployments</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeDeployments.map((deployment) => (
              <div key={deployment.name} className="space-y-2 p-3 rounded-lg bg-muted/30">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{deployment.name}</div>
                  <div className="flex items-center gap-2">
                    {deployment.status === "completed" ? (
                      <Badge variant="outline" className="bg-success/10 text-success border-success">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Completed
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-primary/10 text-primary border-primary">
                        <Clock className="w-3 h-3 mr-1" />
                        Deploying
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Progress value={deployment.progress} className="flex-1" />
                  <span className="text-sm text-muted-foreground">
                    {deployment.progress}%
                  </span>
                </div>
                <div className="text-xs text-muted-foreground">
                  {deployment.devices} devices
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="shadow-card lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/30 transition-colors">
                  <div className="flex-shrink-0">
                    {activity.status === "success" ? (
                      <CheckCircle className="h-5 w-5 text-success" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-warning" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium">{activity.action}</div>
                    <div className="text-sm text-muted-foreground">
                      {activity.device}
                    </div>
                  </div>
                  <div className="flex-shrink-0 text-sm text-muted-foreground">
                    {activity.time}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
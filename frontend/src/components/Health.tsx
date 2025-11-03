import React, { useState, useEffect } from "react";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

interface HealthComponent {
    id: string;
    display_name: string;
    status: "OK" | "ERROR" | "UNKNOWN";
    observed_at: string;
    description: string;
    metrics: Record<string, number>;
}

const Health: React.FC = () => {
    const [components, setComponents] = useState<HealthComponent[]>([]);
    const [overallStatus, setOverallStatus] = useState<string>("UNKNOWN");
    const [loading, setLoading] = useState<boolean>(true);

    // Get health status
    useEffect(() => {
        const fetchHealthStatus = async () => {
            try {
                const statusRes = await fetch(`${API_BASE}/health`);
                const healthStatus = await statusRes.json();
                setOverallStatus(healthStatus.status || "UNKNOWN");
            } catch (error) {
                console.error("Error fetching health status:", error);
                setOverallStatus("ERROR");
            }
        };

        fetchHealthStatus();
    }, []);

    // Get health components
    useEffect(() => {
        const fetchHealthComponents = async () => {
            try {
                const componentRes = await fetch(`${API_BASE}/health/components`);
                const healthComponents = await componentRes.json();
                setComponents(healthComponents.components || []);
            } catch (error) {
                console.error("Error fetching health components:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchHealthComponents();
    }, []);

    const getColor = (status: string) => {
        switch (status) {
            case "OK":
                return "bg-green-500 text-white";
            case "ERROR":
                return "bg-red-500 text-white";
            case "UNKNOWN":
                return "bg-gray-500 text-white";
            default:
                return "bg-gray-500 text-white";
        }
    };

    return (
        <div className="p-4 bg-gray-500 text-white rounded-2xl shadow-lg">
            <h2 className="text-xl font-bold mb-4 text-center">System Health</h2>

            {/* Overall Health */}
            <div className="mb-6 flex items-center text-center justify-center gap-4">
                <span className="font-semibold mr-3">Overall Status:</span>
                <span
                    className={`px-3 py-1 rounded-full text-sm font-medium ${getColor(overallStatus)}`}
                >
                    {overallStatus.toUpperCase()}
                </span>
            </div>

            {/* Components */}
            {loading ? (
                <p className="text-gray-400 text-sm">Loading Health Components...</p>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {components.map((comp) => (
                    <div
                        key={comp.id}
                        className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition"
                    >
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="font-semibold">{comp.display_name}</h3>
                            <span
                                className={`px-3 py-1 rounded-full text-sm font-medium ${getColor(
                                    comp.status
                                )}`}
                            >
                                {comp.status.toUpperCase()}
                            </span>
                        </div>
                        <p className="text-sm text-gray-400 mb-2">{comp.description}</p>
                        <p className="text-xs text-gray-500">
                            Last checked: {new Date(comp.observed_at).toLocaleString()}
                        </p>

                        <div className="mt-3 text-sm text-gray-300">
                            {Object.entries(comp.metrics).map(([key, value]) => (
                                <div key={key} className="flex justify-between">
                                    <span>{key.replace("_", " ")}:</span>
                                    <span>{value}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Health;
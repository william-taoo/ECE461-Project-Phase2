import React, { useState, useEffect } from "react";

interface HealthComponent {
    id: string;
    display_name: string;
    status: "OK" | "BAD";
    observed_at: string;
    description: string;
    metrics: Record<string, number>;
}

const Health: React.FC = () => {
    const [components, setComponents] = useState<HealthComponent[]>([]);
    const [color, setColor] = useState<string>("bg-gray-500 text-white");
    const [loading, setLoading] = useState<boolean>(false);

    // Get health status
    useEffect(() => {
        const fetchHealthStatus = async () => {
            try {
                const statusRes = await fetch("http://localhost:5000/health");
                const healthStatus = await statusRes.json();

                if (healthStatus.status === "OK") {
                    setColor("bg-green-500 text-white");
                } else {
                    setColor("bg-red-500 text-white");
                }
            } catch (error) {
                console.error("Error fetching health status:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchHealthStatus();
    }, []);

    // Get health components
    useEffect(() => {
        const fetchHealthComponents = async () => {
            try {
                const componentRes = await fetch("http://localhost:5000/health/components");
                const healthComponents = await componentRes.json();
                setComponents(healthComponents || []);
            } catch (error) {
                console.error("Error fetching health components:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchHealthComponents();
    }, []);

    if (loading) return <p className="text-gray-400">Loading health data...</p>;

    return (
        <div className="p-4 bg-gray-500 text-white rounded-2xl shadow-lg w-full">
            <h2 className="text-xl font-bold mb-4">System Health</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {components.map((comp) => (
                <div
                    key={comp.id}
                    className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition"
                >
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">{comp.display_name}</h3>
                        <span
                            className={`px-3 py-1 rounded-full text-sm font-medium ${color}`}
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
        </div>
    )
};

export default Health;
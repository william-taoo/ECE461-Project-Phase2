import React, { useState } from "react";

interface Artifact {
    id: string;
    name: string;
    version: string;
    created_at: string;
    description?: string;
}

const Artifacts: React.FC = () => {
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [loading, setLoading] = useState<boolean>(false);

    // Fetch artifacts from backend
    const fetchArtifacts = async () =>{
        try {
            setLoading(true);
            const res = await fetch("http://localhost:5000/artifacts");
            const data = await res.json();
            setArtifacts(data.artifacts || []);
        } catch (error) {
            console.error("Error fetching artifacts:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-4 bg-gray-500 text-white rounded-2xl shadow-lg">
            <div className="flex flex-col items-center justify-between mb-4">
                <h2 className="text-xl font-bold mb-4 text-center">Registered Artifacts</h2>
                <button
                    onClick={fetchArtifacts}
                    className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition"
                >
                    {loading ? "Loading..." : "Reload"}
                </button>
            </div>

            {loading ? (
                <p className="text-gray-400 text-sm">Fetching artifacts...</p>
            ) : artifacts.length > 0 ? (
                <div className="max-h-[32rem] overflow-y-auto pr-2">
                    <ul className="space-y-3">
                    {artifacts.map((a) => (
                        <li
                            key={a.id}
                            className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition"
                        >
                            <div className="flex items-center justify-between">
                                <span className="font-semibold">{a.name}</span>
                                <span className="text-sm text-gray-400">
                                v{a.version}
                                </span>
                            </div>
                            {a.description && (
                                <p className="text-sm text-gray-400 mt-1">
                                    {a.description}
                                </p>
                            )}
                            <p className="text-xs text-gray-500 mt-2">
                                Added: {new Date(a.created_at).toLocaleString()}
                            </p>
                        </li>
                    ))}
                    </ul>
                </div>
            ) : (
                <p className="text-white text-sm text-center">No artifacts registered yet.</p>
            )}
        </div>
    )
};

export default Artifacts;
import React, { useState } from "react";
import Upload from "./Upload";
import Rate from "./Rate";
import Download from "./Download";
import SearchByNameType from "./SearchByNameType";

interface MetaData {
    id: string;
    name: string;
    version: string;
    type: string;
}

interface Data {
    url: string;
}

interface Artifact {
    metadata: MetaData;
    data: Data;
}

const Artifacts: React.FC = () => {
    const [artifacts, setArtifacts] = useState<Artifact[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [selectedResult, setSelectedResult] = useState<any | null>(null);

    // Fetch artifacts from backend
    const fetchArtifacts = async () =>{
        try {
            setLoading(true);
            const res = await fetch("http://localhost:5000/artifacts", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify([
                    {
                        name: "*", // Wildcard to get all artifacts
                        type: null // or "model" / "dataset" if you want to filter
                    }
                ])
            });
            const data = await res.json();
            setArtifacts(data || []);
        } catch (error) {
            console.error("Error fetching artifacts:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-4 bg-gray-500 text-white rounded-2xl shadow-lg">
            <h2 className="text-xl font-bold mb-4 text-center">Registered Artifacts</h2>
            
            <div className="flex flex-row items-center justify-center gap-3 mb-4">
                <Upload />
                <SearchByNameType 
                    result={(data) => setArtifacts(data)}
                />
            </div>

            {loading ? (
                <p className="text-gray-400 text-sm">Fetching artifacts...</p>
            ) : artifacts.length > 0 ? (
                <div className="max-h-[32rem] overflow-y-auto pr-2">
                    <ul className="space-y-3">
                        {artifacts.map((a) => (
                            <li
                                key={a.metadata.id}
                                className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition"
                            >
                                <div className="flex items-center justify-between">
                                    <span className="font-semibold">{a.metadata.name}</span>
                                    <span className="text-sm text-gray-400">
                                    v{a.metadata.version}
                                    </span>
                                </div>
                                <div className="text-sm text-gray-400">
                                    ID: {a.metadata.id}
                                </div>
                                <div className="text-sm text-gray-400">
                                    Type: {a.metadata.type}
                                </div>
                                <div className="text-sm text-gray-400 break-all">
                                    URL: {a.data.url}
                                </div>

                                <div className="mt-3 flex flex-row gap-3">
                                    <Rate 
                                        artifactID={a.metadata.id}
                                        result={
                                            (data) => setSelectedResult(data)
                                        }
                                    />
                                    <Download />
                                </div>
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
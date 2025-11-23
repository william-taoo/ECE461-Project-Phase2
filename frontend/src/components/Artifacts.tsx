import React, { useState } from "react";
import Upload from "./Upload";
import Rate from "./Rate";
import Download from "./Download";
import SearchByQuery from "./SearchByQuery";
import ModelByName from "./ModelByName";

interface MetaData {
    id: string;
    name: string;
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
    const [rateResult, setRateResult] = useState<any | null>(null);
    const [searchResults, setSearchResults] = useState<MetaData[]>([]);

    return (
        <div className="p-4 bg-gray-500 text-white rounded-2xl shadow-lg">
            <h2 className="text-xl font-bold mb-4 text-center">Registered Artifacts</h2>
            
            <div className="flex flex-row items-center justify-center gap-3 mb-4">
                <Upload />
                <SearchByQuery result={(data) => setArtifacts(data)} />
                <ModelByName onResults={(items) => setSearchResults(items)} />
            </div>

            {searchResults.length > 0 && (
                <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2">Search Results (by name)</h3>
                    <div className="max-h-[20rem] overflow-y-auto pr-2">
                        <ul className="space-y-3">
                        {searchResults.map((m) => (
                            <li
                                key={m.id}
                                className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition"
                            >
                                <div className="text-sm text-gray-400">ID: {m.id}</div>
                                <div className="text-sm text-gray-400">Type: {m.type}</div>

                                <div className="mt-3 flex flex-row gap-3">
                                    <Rate artifactID={m.id} result={(data) => setRateResult(data)} />
                                    {/* No Download button here because the name-only endpoint
                                        doesn't return a URL. If you want Download, fetch by ID
                                        to get the full Artifact (with data.url) first. */}
                                </div>
                            </li>
                        ))}
                        </ul>
                    </div>
                </div>
            )}
            
            {artifacts.length > 0 ? (
                <div className="max-h-[32rem] overflow-y-auto pr-2">
                    <ul className="space-y-3">
                        {artifacts.map((a) => (
                            <li
                                key={a.metadata.id}
                                className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition"
                            >
                                <div className="flex items-center justify-between">
                                    <span className="font-semibold">{a.metadata.name}</span>
                                    <span className="text-sm text-gray-400"></span>
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
                                            (data) => setRateResult(data)
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
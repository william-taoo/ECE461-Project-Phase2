import React, { useState } from "react";
import Upload from "./Upload";
import Rate from "./Rate";
import Download from "./Download";
import SearchByQuery from "./SearchByQuery";
import ModelByName from "./ModelByName";
import InspectArtifactModal from "./InspectArtifact";
import Regex from "./Regex";

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

interface ArtifactProps {
    onResult: (data: any) => void;
}

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const Artifacts: React.FC<ArtifactProps> = ({ onResult }) => {
    const [queryArtifacts, setQueryArtifacts] = useState<Artifact[]>([]);
    const [searchByNameArtifacts, setSearchByNameArtifacts] = useState<MetaData[]>([]);
    const [regexArtifacts, setRegexArtifacts] = useState<MetaData[]>([]);
    const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
    const [showInspectModal, setShowInspectModal] = useState<boolean>(false);
    const [isSearchByQuery, setIsSearchByQuery] = useState<boolean>(false);
    const [isSearchByName, setIsSearchByName] = useState<boolean>(false);
    const [isSearchByRegex, setIsSearchByRegex] = useState<boolean>(false);

    const inspectArtifact = async (id: string, type: string) => {
        try {
            const endpoint = `${API_BASE}/artifacts/${type}/${id}`;
            const res = await fetch(endpoint);
            if (!res.ok) throw new Error("Failed to fetch artifact");
            const data = await res.json();
            setSelectedArtifact(data);
            setShowInspectModal(true);
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="p-4 bg-gray-500 text-white rounded-2xl shadow-lg">
            <h2 className="text-xl font-bold mb-4 text-center">Registered Artifacts</h2>
            
            <div className="flex flex-row items-center justify-center gap-3 mb-4">
                <Upload />
                <SearchByQuery 
                    result={(data) => {
                        setQueryArtifacts(data);
                        setSearchByNameArtifacts([]);
                        setIsSearchByQuery(true);
                        setIsSearchByName(false);
                        setIsSearchByRegex(false);
                    }}
                />
                <ModelByName 
                    onResults={(items) => {
                        setSearchByNameArtifacts(items);
                        setQueryArtifacts([]);
                        setIsSearchByQuery(false);
                        setIsSearchByName(true);
                        setIsSearchByRegex(false);
                    }}
                />
                <Regex
                    result={(data) => {
                        setRegexArtifacts(data);
                        setSearchByNameArtifacts([]);
                        setIsSearchByQuery(false);
                        setIsSearchByName(false);
                        setIsSearchByRegex(true);
                    }}
                />
            </div>

            {isSearchByName && searchByNameArtifacts.length > 0 && (
                <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2">Search Results (by name)</h3>
                    <div className="max-h-[20rem] overflow-y-auto pr-2">
                        <ul className="space-y-3">
                        {searchByNameArtifacts.map((m) => (
                            <li
                                key={m.id}
                                className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition"
                                onClick={() => inspectArtifact(m.id, m.type)}
                            >
                                <div className="font-semibold">{m.name}</div>
                            </li>
                        ))}
                        </ul>
                    </div>
                </div>
            )}

            {isSearchByQuery && queryArtifacts.length > 0 && (
                <div className="max-h-[32rem] overflow-y-auto pr-2">
                    <h3 className="text-lg font-semibold mb-2">Search Results (by query)</h3>
                    <ul className="space-y-3">
                        {queryArtifacts.map((a) => (
                            <li
                                key={a.metadata.id}
                                className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition cursor-pointer"
                                onClick={() => inspectArtifact(a.metadata.id, a.metadata.type)}
                            >
                                <div className="font-semibold">{a.metadata.name}</div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {isSearchByRegex && regexArtifacts.length > 0 && (
                <div className="max-h-[32rem] overflow-y-auto pr-2">
                    <h3 className="text-lg font-semibold mb-2">Search Results (by regex)</h3>
                    <ul className="space-y-3">
                        {regexArtifacts.map((a) => (
                            <li
                                key={a.id}
                                className="p-4 bg-gray-800 rounded-xl border border-gray-700 hover:border-gray-600 transition cursor-pointer"
                                onClick={() => inspectArtifact(a.id, a.type)}
                            >
                                <div className="font-semibold">{a.name}</div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {!isSearchByQuery && !isSearchByName && !isSearchByRegex &&(
                <p className="text-gray-300 text-center">No artifacts to display. Please use the search options above.</p>
            )}

            <InspectArtifactModal
                show={showInspectModal}
                onClose={() => setShowInspectModal(false)}
                artifact={selectedArtifact}
                onResult={onResult}
            />
        </div>
    )
};

export default Artifacts;
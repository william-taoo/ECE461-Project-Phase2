import React, { useState } from "react";

interface ResultPanelProps {
    result: any | null;
}

const ResultPanel: React.FC<ResultPanelProps> = ({ result }) => {

    return (
        <div className="w-full mt-6">
            <div className="p-6 bg-gray-800 rounded-xl border border-gray-700 shadow-lg hover:border-gray-600 transition w-full">
                
                <h2 className="text-2xl font-bold text-gray-100 mb-4">
                    {!result ? "Result Panel" : result.type === "Audit" ? "Audit Results" : "Lineage Results"}
                </h2>

                {result ? (
                    <div className="max-h-[400px] overflow-y-auto bg-gray-900 p-4 rounded-xl border border-gray-700">
                        <pre className="whitespace-pre-wrap text-sm text-gray-300">
                            {JSON.stringify(result, null, 2)}
                        </pre>
                    </div>
                ) : (
                    <p className="text-gray-400 text-sm">
                        No results yet. Run an audit or get the lineage graph an artifact.
                    </p>
                )}
            </div>
        </div>
    );
};

export default ResultPanel;

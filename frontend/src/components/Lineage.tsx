import React from "react";
import Button from "react-bootstrap/Button";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

interface LineageProps {
    artifact_id: string;
    onClose: () => void;
    onResult: (type: string, data: any) => void;
}

const Lineage: React.FC<LineageProps> = ({ artifact_id, onClose, onResult }) => {
    const handleLineage = async () => {
        try {
            const res = await fetch(`${API_BASE}/artifact/model/${artifact_id}/lineage`);
            const data = await res.json();
            onResult("Lineage", data);
            onClose();
        } catch (error) {
            console.error("Error getting lineage for the model:", error);
        }
    };

    return (
        <Button 
            variant="info"
            onClick={handleLineage}
        >
            View Lineage of Artifact
        </Button>
    );
};

export default Lineage;
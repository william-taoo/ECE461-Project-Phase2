import React from "react";
import Button from "react-bootstrap/Button";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

interface AuditProps {
    artifact_type: string;
    artifact_id: string;
    onClose: () => void;
    onResult: (type: string, data: any) => void;
}

const Audit: React.FC<AuditProps> = ({ artifact_type, artifact_id, onClose, onResult }) => {
    const handleAudit = async () => {
        try {
            const res = await fetch(`${API_BASE}/artifact/${artifact_type}/${artifact_id}/audit`);
            const data = await res.json();
            onResult("Audit", data);
            onClose();
        } catch (error) {
            console.error("Error auditing artifact:", error);
        }
    };

    return (
        <Button 
            variant="warning"
            onClick={handleAudit}
        >
            Audit Artifact
        </Button>
    );
};

export default Audit;
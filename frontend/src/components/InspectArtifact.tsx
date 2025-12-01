import React, { useState, useEffect } from "react";
import { Modal, Button } from "react-bootstrap";
import Download from "./Download";
import Audit from "./Audit";
import Lineage from "./Lineage";

interface InspectArtifactModalProps {
    show: boolean;
    onClose: () => void;
    artifact: any | null;
    onResult: (data: any) => void;
}

interface Result {
    type: string;
    data: any;
}

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const InspectArtifactModal: React.FC<InspectArtifactModalProps> = ({ show, onClose, artifact, onResult }) => {
    const [updatedUrl, setUpdatedUrl] = useState<string>("");
    const [auditResult, setAuditResult] = useState<Result | null>(null);
    const [lineageResult, setLineageResult] = useState<Result | null>(null);
    
    useEffect(() => {
        if (auditResult) {
            onResult(auditResult);
        }
    }, [auditResult]);

    useEffect(() => {
        if (lineageResult) {
            onResult(lineageResult);
        }
    }, [lineageResult]);

    if (!artifact) return null;

    const handleUpdate = async () => {
        try {
            const endpoint = `${API_BASE}/artifacts/${artifact.metadata.type}/${artifact.metadata.id}`;
            const res = await fetch(endpoint, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ url: updatedUrl }),
            });
            const data = await res.json();
            onClose();
        } catch (err) {
            console.error(err);
            alert("Update failed");
        }
    };

    return (
        <Modal show={show} onHide={onClose} centered size="lg">
            <Modal.Header closeButton>
                <Modal.Title>Artifact Details</Modal.Title>
            </Modal.Header>

            <Modal.Body>
                <p><strong>Name:</strong> {artifact.metadata.name}</p>
                <p><strong>ID:</strong> {artifact.metadata.id}</p>
                <p><strong>Type:</strong> {artifact.metadata.type}</p>
                <div className="mt-3">
                    <label className="font-semibold">URL:</label>
                    <input
                        type="text"
                        className="form-control mt-2"
                        value={updatedUrl}
                        placeholder={artifact.data.url}
                        onChange={(e) => setUpdatedUrl(e.target.value)}
                    />
                </div>
            </Modal.Body>

            <Modal.Footer className="d-flex justify-content-center flex-wrap gap-2">
                <Button variant="secondary" onClick={onClose}>
                    Close
                </Button>
                <Button variant="primary" onClick={handleUpdate}>
                    Update URL
                </Button>
                <Download modelID={artifact.metadata.id} />
                <Audit 
                    artifact_type={artifact.metadata.type}
                    artifact_id={artifact.metadata.id}
                    onResult={(type, data) => setAuditResult({ type, data })}
                    onClose={onClose}
                />
                <Lineage 
                    artifact_id={artifact.metadata.id}
                    onResult={(type, data) => setLineageResult({ type, data })}
                    onClose={onClose}
                />
            </Modal.Footer>
        </Modal>
    );
};

export default InspectArtifactModal;

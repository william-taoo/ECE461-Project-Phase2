import React, { useState } from "react";
import { Modal, Button } from "react-bootstrap";

interface InspectArtifactModalProps {
    show: boolean;
    onClose: () => void;
    artifact: any | null;
}

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const InspectArtifactModal: React.FC<InspectArtifactModalProps> = ({ show, onClose, artifact }) => {
    const [updatedUrl, setUpdatedUrl] = useState<string>("");
    
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
        <Modal show={show} onHide={onClose} centered>
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

            <Modal.Footer>
                <Button variant="secondary" onClick={onClose}>
                    Close
                </Button>
                <Button variant="primary" onClick={handleUpdate}>
                    Update URL
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default InspectArtifactModal;

import React from "react";
import { Modal, Button } from "react-bootstrap";

interface InspectArtifactModalProps {
    show: boolean;
    onClose: () => void;
    artifact: any | null;
}

const InspectArtifactModal: React.FC<InspectArtifactModalProps> = ({ show, onClose, artifact }) => {
    if (!artifact) return null;

    return (
        <Modal show={show} onHide={onClose} centered>
            <Modal.Header closeButton>
                <Modal.Title>Artifact Details</Modal.Title>
            </Modal.Header>

            <Modal.Body>
                <p><strong>Name:</strong> {artifact.metadata.name}</p>
                <p><strong>ID:</strong> {artifact.metadata.id}</p>
                <p><strong>Type:</strong> {artifact.metadata.type}</p>
                <p><strong>URL:</strong></p>
                <p className="break-all text-blue-400">{artifact.data.url}</p>
            </Modal.Body>

            <Modal.Footer>
                <Button variant="secondary" onClick={onClose}>
                    Close
                </Button>
            </Modal.Footer>
        </Modal>
    );
};

export default InspectArtifactModal;

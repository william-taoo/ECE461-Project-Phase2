import React from "react";
import Button from "react-bootstrap/Button";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

interface DeleteProps {
    artifact_type: string;
    artifactID: string;
    onClose: () => void;
}

const Delete: React.FC<DeleteProps> = ({ artifact_type, artifactID, onClose }) => {
    const handleDelete = async () => {
        try {
            await fetch(`${API_BASE}/artifacts/${artifact_type}/${artifactID}`, {
                method: "DELETE",
            });
            alert("Registry reset.");
            onClose();
        } catch (error) {
            console.error("Error deleting artifact:", error);
        }
    };

    return (
        <Button 
            variant="danger"
            onClick={handleDelete}
        >
            Delete Artifact
        </Button>
    );
};

export default Delete;

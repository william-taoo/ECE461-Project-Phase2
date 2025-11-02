import React, { useState } from "react";
import { Button, Modal, Form } from "react-bootstrap";
import { inferArtifactType } from "../utils/artifactType";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const Upload: React.FC = () => {
    const [show, setShow] = useState(false);
    const [modelURL, setModelURL] = useState<string>("");

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const handleUpload = async () => {
        if (!modelURL) {
            alert("Please enter a model URL.");
            return;
        }

        // Link Flask Upload API
        let type: "model" | "dataset" | "code";
        try {
            type = inferArtifactType(modelURL);
        } catch (e: any) {
            alert(e?.message || "Could not infer artifact type from URL.");
            return;
        }
        
        try {
            const endpoint = `${API_BASE}/artifact/${type}`;
            const response = await fetch(endpoint, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ url: modelURL }),
            });
      
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
              const msg = data?.error || response.statusText;
              alert(`Upload failed (${response.status}): ${msg}`);
              return;
            }
      
            alert(`Uploaded as ${type}. ID: ${data?.metadata?.id ?? "(unknown)"}`);
            handleClose();
            setModelURL("");
        } catch (err) {
            console.error("Upload failed:", err);
            alert("Network or server error.");
        }
    };

    return (
        <>
            <Button
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded"
                onClick={handleShow}
            >
                Upload Model/Dataset/Code
            </Button>

            <Modal 
                show={show} 
                onHide={handleClose} 
                centered
            >
                <Modal.Header className="bg-gray-300" closeButton>
                    <Modal.Title>Upload Artifact</Modal.Title>
                </Modal.Header>

                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3">
                            <Form.Label>Source URL</Form.Label>
                            <Form.Control
                                type="text"
                                value={modelURL}
                                onChange={(e) => setModelURL(e.target.value)}
                                placeholder="Ex: https://huggingface.co/google-bert/bert-base-uncased"
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>

                <Modal.Footer>
                    <div className="flex justify-between w-full">
                        <Button variant="secondary" onClick={handleClose}>
                            Close
                        </Button>
                        <Button variant="primary" onClick={handleUpload}>
                            Upload
                        </Button>
                    </div>
                </Modal.Footer>
            </Modal>
        </>
    );
};

export default Upload;

import React, { useState } from "react";
import { Button, Modal, Form } from "react-bootstrap";

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
        try {
            const response = await fetch("http://localhost:5000/upload", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ url: modelURL }),
            });

            const data = await response.json()

            if (!response.ok) {
                alert("Error: " + data.error);
            } else {
                alert("Model uploaded successfully!");
                handleClose(); // Close modal
                setModelURL("");
            }
        } catch (err) {
            console.error("Upload failed: ", err);
            alert("Error uploading model...");
        }
    };

    return (
        <>
            <Button
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded"
                onClick={handleShow}
            >
                Upload Model
            </Button>

            <Modal 
                show={show} 
                onHide={handleClose} 
                centered
            >
                <Modal.Header className="bg-gray-300" closeButton>
                    <Modal.Title>Upload Model</Modal.Title>
                </Modal.Header>

                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3">
                            <Form.Label>Model URL</Form.Label>
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

import React, { useState } from "react";
import { Button, Modal, Form } from "react-bootstrap";

const Upload: React.FC = () => {
    const [show, setShow] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [modelName, setModelName] = useState("");

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file || !modelName) {
            alert("Please select a file and enter a model name.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("modelName", modelName);

        // Link Flask Upload API
        try {
            const response = await fetch("http://localhost:5000/upload", {
                method: "POST",
                body: formData,
            });

            const data = await response.json()

            if (!response.ok) {
                alert("Error: " + data.error);
            } else {
                alert("Model uploaded successfully!");
                handleClose(); // Close modal
                setFile(null);
                setModelName("");
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
                            <Form.Label>Model Name</Form.Label>
                            <Form.Control
                                type="text"
                                value={modelName}
                                onChange={(e) => setModelName(e.target.value)}
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Model File</Form.Label>
                            <Form.Control type="file" onChange={handleFileChange} />
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

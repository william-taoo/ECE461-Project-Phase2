import React, { useState } from "react";
import { Button, Modal, Form } from "react-bootstrap";

interface SearchByRegexProps {
    result: (data: any) => void;
}

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const Regex: React.FC<SearchByRegexProps> = ({ result }) => {
    const [show, setShow] = useState<boolean>(false);
    const [regex, setRegex] = useState<string>("");

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const handleRegex = async () => {
        try {
            const query = {
                regex: (regex || "*").trim(),
            };
            const endpoint = `${API_BASE}/artifact/byRegEx`;
            const res = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(query),
            });
            const text = await res.text();
            if (!res.ok) {
                let msg = "Search by RegEx failed.";
                try { msg = JSON.parse(text)?.error ?? msg; } catch {}
                throw new Error(`${msg} (${res.status})`);
            }
            const data = JSON.parse(text);
            result(data);
        } catch (error) {
            console.error("Error searching artifacts:", error);
            alert("Error searching artifacts.");
        } finally {
            handleClose();
        }
    }
    
    return (
        <>
            <Button
                className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded"
                onClick={handleShow}
            >
                Search by Regex
            </Button>

            <Modal 
                show={show} 
                onHide={handleClose} 
                centered
            >
                <Modal.Header className="bg-gray-300" closeButton>
                    <Modal.Title>Search Artifact</Modal.Title>
                </Modal.Header>

                <Modal.Body>
                    <Form onSubmit={(e) => { e.preventDefault(); handleRegex(); }}>
                        <Form.Group className="mb-3">
                            <Form.Label>Enter RegEx Pattern</Form.Label>
                            <Form.Control
                                type="text"
                                value={regex}
                                onChange={(e) => setRegex(e.target.value)}
                                placeholder='.*?(audience|bert).*'
                                required={true}
                            />
                        </Form.Group>
                    </Form>
                </Modal.Body>

                <Modal.Footer>
                    <div className="flex justify-between w-full">
                        <Button variant="secondary" onClick={handleClose}>
                            Close
                        </Button>
                        <Button 
                            variant="primary"
                            type="submit"
                            onClick={handleRegex}
                        >
                            Search
                        </Button>
                    </div>
                </Modal.Footer>
            </Modal>
        </>
    );
};

export default Regex;
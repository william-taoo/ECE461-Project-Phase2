import React, { useState } from "react";
import { Button, Modal, Form } from "react-bootstrap";

interface SearchByQueryProps {
    result: (data: any) => void;
}

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const SearchByQuery: React.FC<SearchByQueryProps> = ({ result }) => {
    const [show, setShow] = useState<boolean>(false);
    const [searchName, setSearchName] = useState<string>("");
    const [searchType, setSearchType] = useState<string>("all");

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const handleSearch = async () => {
        try {
            const query = {
                name: (searchName || "*").trim(),
                type: searchType === "all" ? [] : searchType,
            };

            const endpoint = `${API_BASE}/artifacts`;
            const res = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify([query]),
            });
            const text = await res.text();
            if (!res.ok) {
                let msg = "Search failed.";
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
                Search by Query
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
                    <Form onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
                        <Form.Group className="mb-3">
                            <Form.Label>Name</Form.Label>
                            <Form.Control
                                type="text"
                                value={searchName}
                                onChange={(e) => setSearchName(e.target.value)}
                                placeholder='Ex: bert-base-uncased (or "*" for all)'
                                required={true}
                            />
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>Type</Form.Label>
                            <Form.Select
                                value={searchType}
                                onChange={(e) => setSearchType(e.target.value)}
                            >
                                <option value="all">All</option>
                                <option value="model">Model</option>
                                <option value="dataset">Dataset</option>
                                <option value="code">Code</option>
                            </Form.Select>
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
                            onClick={handleSearch}
                        >
                            Search
                        </Button>
                    </div>
                </Modal.Footer>
            </Modal>
        </>
    );
};

export default SearchByQuery;

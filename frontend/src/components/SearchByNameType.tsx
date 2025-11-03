import React, { useState } from "react";
import { Button, Modal, Form } from "react-bootstrap";

interface SearchByNameTypeProps {
    result: (data: any) => void;
}

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

const SearchByNameType: React.FC<SearchByNameTypeProps> = ({ result }) => {
    const [show, setShow] = useState(false);
    const [searchName, setSearchName] = useState<string>("");
    const [searchType, setSearchType] = useState<string>("all");
    const [searchVersion, setSearchVersion] = useState<string>("");

    const handleClose = () => setShow(false);
    const handleShow = () => setShow(true);

    const handleSearch = async () => {
        try {
            const query: any = {
                    name: (searchName || "*").trim(),
            };
            if (searchVersion.trim()) {
                    query.version = searchVersion.trim();
            }
            if (searchType !== "all") {
                    query.type = searchType;
            }

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
                        <Form.Group className="mb-1">
                            <Form.Label>Version (SemverRange)</Form.Label>
                            <Form.Control
                                type="text"
                                value={searchVersion}
                                onChange={(e) => setSearchVersion(e.target.value)}
                                placeholder={`Examples: 
0.3.0 (exact) 
1.* (wildcard) 
>=1.2.0 (comparator) 
^1.2.3 (caret) 
~1.4.0 (tilde)
`}
                            />
                            <Form.Text>
                                Leave blank to ignore version. Use only one style (exact, wildcard, comparator, caret, or tilde).
                            </Form.Text>
                            </Form.Group>
                    </Form>
                </Modal.Body>

                <Modal.Footer>
                    <div className="flex justify-between w-full">
                        <Button variant="secondary" onClick={handleClose}>
                            Close
                        </Button>
                        <Button variant="primary" onClick={handleSearch}>
                            Search
                        </Button>
                    </div>
                </Modal.Footer>
            </Modal>
        </>
    );
};

export default SearchByNameType;

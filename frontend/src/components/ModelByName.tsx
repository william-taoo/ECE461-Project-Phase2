import React, { useState } from "react";
import { Button, Modal, Form } from "react-bootstrap";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

export interface MetaData {
    name: string;
    id: string;
    type: string;
}

interface Props {
    onResults?: (items: MetaData[]) => void;
}

const ModelByName: React.FC<Props> = ({ onResults }) => {
    const [show, setShow] = useState(false);
    const [name, setName] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<MetaData[]>([]);

    const handleClose = () => {
        setShow(false);
        setError(null);
        setResults([]);
        setName("");
    };
    const handleShow = () => setShow(true);
    const search = async () => {
        const q = name.trim();
        if (!q) {
            setError("Please enter an artifact name.");
            return;
        }
        setLoading(true);
        setError(null);
        setResults([]);
    
        try {
            // const token =
            //     localStorage.getItem("authToken") ||
            //     process.env.REACT_APP_AUTH_TOKEN ||
            //     "bearer demo-token";
    
            const res = await fetch(`${API_BASE}/artifact/byName/${encodeURIComponent(q)}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
                },
            });
    
          const text = await res.text();
          if (!res.ok) {
            let msg = "Search failed.";
            try { msg = JSON.parse(text)?.error ?? msg; } catch { /* noop */ }
            throw new Error(`${msg} (${res.status})`);
          }
    
          const data: MetaData[] = JSON.parse(text);
          setResults(data);
          onResults?.(data);
        } catch (e: any) {
          setError(e?.message ?? "Network or server error.");
        } finally {
          setLoading(false);
          handleClose();
        }
    };

    return (
        <>
          <Button
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded"
            onClick={handleShow}
          >
            Search by Name
          </Button>
    
          <Modal show={show} onHide={handleClose} centered>
            <Modal.Header className="bg-gray-300" closeButton>
              <Modal.Title>Search Artifact by Name</Modal.Title>
            </Modal.Header>
    
            <Modal.Body>
              <Form onSubmit={(e) => { e.preventDefault(); search(); }}>
                <Form.Group className="mb-3">
                  <Form.Label>Artifact Name</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="e.g., audience-classifier"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    autoFocus
                  />
                </Form.Group>
                {error && <div className="text-red-600 text-sm">{error}</div>}
              </Form>
    
              {/* {results.length > 0 && (
                <div className="mt-3 overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left border-b">
                        <th className="py-2 pr-4">Name</th>
                        <th className="py-2 pr-4">Type</th>
                        <th className="py-2">ID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map(r => (
                        <tr key={r.id} className="border-b">
                          <td className="py-2 pr-4">{r.name}</td>
                          <td className="py-2 pr-4">{r.type}</td>
                          <td className="py-2 font-mono break-all">{r.id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )} */}
            </Modal.Body>
    
                <Modal.Footer>
                    <div className="flex justify-between w-full">
                        <Button variant="secondary" onClick={handleClose}>Close</Button>
                        <Button variant="primary" onClick={search} disabled={loading}>
                            {loading ? "Searching..." : "Search"}
                        </Button>
                    </div>
                </Modal.Footer>
            </Modal>
        </>
    );
};
    
export default ModelByName;
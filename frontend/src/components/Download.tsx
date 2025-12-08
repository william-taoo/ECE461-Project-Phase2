import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import Spinner from "react-bootstrap/Spinner";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

interface RateProps {
    modelID: string;
}

const Download: React.FC<RateProps> = ({ modelID }) => {
    const [downloading, setDownloading] = useState(false);

    const handleDownload = async () => {
        try {
            setDownloading(true);

            const res = await fetch(`${API_BASE}/download/${modelID}`);

            if (!res.ok) {
                console.error("Failed to download:", await res.text());
                setDownloading(false);
                return;
            }

            // Extract filename from header
            const disposition = res.headers.get("Content-Disposition");
            let filename = `${modelID}.zip`;

            if (disposition && disposition.includes("filename=")) {
                const match = disposition.match(/filename="?(.+)"?/);
                if (match && match[1]) filename = match[1];
            }

            // Download blob
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();

            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Error downloading model:", error);
        } finally {
            setDownloading(false);
        }
    };

    return (
        <Button 
            variant="success"
            onClick={handleDownload}
            disabled={downloading}
            style={{ minWidth: "150px" }} // keeps size stable when text changes
        >
            {downloading ? (
                <>
                    <Spinner
                        as="span"
                        animation="border"
                        size="sm"
                        role="status"
                        aria-hidden="true"
                        className="me-2"
                    />
                    Downloading...
                </>
            ) : (
                "Download Model"
            )}
        </Button>
    );
};

export default Download;

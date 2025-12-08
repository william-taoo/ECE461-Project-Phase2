import React from "react";
import Button from "react-bootstrap/Button";

const API_BASE = (process.env.REACT_APP_API_BASE ?? "http://localhost:5000").replace(/\/+$/, "");

interface RateProps {
    modelID: string;
}

const Download: React.FC<RateProps> = ({ modelID }) => {

    const handleDownload = async () => {
        try {
            const res = await fetch(`${API_BASE}/download/${modelID}`);

            if (!res.ok) {
                console.error("Failed to download:", await res.text());
                return;
            }

            // Extract filename from headers
            const disposition = res.headers.get("Content-Disposition");
            let filename = `${modelID}.zip`;

            if (disposition && disposition.includes("filename=")) {
                const match = disposition.match(/filename="?(.+)"?/);
                if (match && match[1]) filename = match[1];
            }

            // Get file blob
            const blob = await res.blob();

            // Create URL for blob
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
        }
    };

    return (
        <Button variant="success" onClick={handleDownload}>
            Download Model
        </Button>
    );
};

export default Download;

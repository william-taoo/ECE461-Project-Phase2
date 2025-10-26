import React from "react";
import Button from "react-bootstrap/Button";

const Download: React.FC = () => {
    const handleDownload = () => {
        console.log("Download button clicked");
        // Link Flask API
    };

    return (
        <Button 
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded"
            onClick={handleDownload}
        >
            Download Model
        </Button>
    );
};

export default Download;

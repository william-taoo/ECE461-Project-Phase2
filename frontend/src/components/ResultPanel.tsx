import React, { useState } from "react";

interface ResultPanelProps {
    result: any | null;
}

const ResultPanel: React.FC<ResultPanelProps> = ({ result }) => {
    if (!result) return null;

    return (
        <></>
    );
};

export default ResultPanel;

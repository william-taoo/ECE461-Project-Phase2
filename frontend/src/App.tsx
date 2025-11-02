import 'bootstrap/dist/css/bootstrap.min.css';
import Upload from './components/Upload';
import Rate from './components/Rate';
import Download from './components/Download';
import Health from './components/Health';
import Artifacts from './components/Artifacts';

function App() {

    return (
        <div className="min-h-screen flex flex-col items-center bg-gray-300 px-6 py-8">
            <h1 className="text-4xl font-bold text-gray-800 text-center mb-8">Registry Dashboard</h1>
        
            {/* Health and Artifact Column Components */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full mb-8">
                <Health />
                <Artifacts />
            </div>

            <div className="flex gap-12">
                <Upload />
                <Rate />
                <Download />
            </div>

            
        </div>
    );
}

export default App;

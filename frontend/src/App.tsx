import 'bootstrap/dist/css/bootstrap.min.css';
import Upload from './components/Upload';
import Rate from './components/Rate';
import Download from './components/Download';

function App() {

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-300">
            <h1 className="text-4xl font-bold text-gray-800 mb-8">Model Dashboard</h1>
        
            <div className="flex gap-12">
                <Upload />
                <Rate />
                <Download />
            </div>
        </div>
    );
}

export default App;

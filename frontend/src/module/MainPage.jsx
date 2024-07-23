import React, { useState } from 'react';
import Header from '../components/Header';
import Title from '../components/Title';
import Border from '../components/Border';
import Button from '../components/Button';
import axios from 'axios';
import Card from '../components/Card';

const MainPage = () => {
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState(null);
  const [error, setError] = useState(null);
  const [isConverting, setIsConverting] = useState(false);
  const [convertedFileUrl, setConvertedFileUrl] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setFileName(selectedFile ? selectedFile.name : null);
    setError(null); // Reset error when a new file is selected
    setConvertedFileUrl(null); // Reset converted file URL when a new file is selected
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError("Harap pilih file terlebih dahulu.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsConverting(true); // Mulai animasi konversi

    try {
      const response = await axios.post("http://localhost:5000/convert", formData, {
        responseType: "blob",
      });

      if (response.headers['content-type'] === 'application/pdf') {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        setConvertedFileUrl(url); // Simpan URL file yang dikonversi
      } else {
        const reader = new FileReader();
        reader.onload = () => {
          const errorResponse = JSON.parse(reader.result);
          setError(errorResponse.error);
        };
        reader.readAsText(response.data);
      }
      setIsConverting(false); // Hentikan animasi konversi
    } catch (error) {
      console.error("Error converting file:", error);
      setError(error.response?.data?.error || "An unknown error occurred.");
      setIsConverting(false); // Hentikan animasi konversi
    }
  };

  const handleDownload = () => {
    const link = document.createElement("a");
    link.href = convertedFileUrl;
    link.setAttribute("download", "converted.pdf");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className='container mx-auto mt-20 font-sans'>
      <Header text="Konversi Skripsi Menjadi Jurnal Ilmiah Secara Otomatis" />
      <div className="mt-8">
        <Title text="Unggah Skripsi" />
      </div>
      <div className="mt-8">
        <form onSubmit={handleSubmit}>
          <Border handleFileChange={handleFileChange} fileName={fileName} />
          <Button text="KONVERSI" fullWidth={true} />
        </form>
        {error && (
          <div className="mt-4 text-red-500 text-center">
            {error}
          </div>
        )}
        {isConverting && (
          <div className="mt-4 text-center">
            <div className="loader mx-auto"></div>
            <p>Konversi sedang berlangsung...</p>
          </div>
        )}
        {convertedFileUrl && (
          <div className="mt-4 text-center">
            <Button 
              text="DOWNLOAD" 
              fullWidth={true} 
              onClick={handleDownload}
            />
          </div>
        )}
      </div>

      <div className='w-full'>
        <Card />
      </div>
    </div>
  );
}

export default MainPage;

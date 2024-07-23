import React from 'react';
import Button from './Button';
import DescText from './DescText';

const Border = ({ handleFileChange, fileName }) => {
  const fileInputRef = React.createRef();

  const handleButtonClick = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="border-dashed border-2 border-primary w-9/12 h-48 flex items-center justify-center mx-auto">
      <div className="flex flex-col items-center">
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <Button text="Pilih File" onClick={handleButtonClick} type="button" />
        <DescText text="File yang diterima: docx" />
        {fileName && (
          <div className="mt-2 text-center text-gray-600">
            File dipilih: {fileName}
          </div>
        )}
      </div>
    </div>
  );
}

export default Border;

import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { dcc } from 'dash-renderer';

const CustomVideoUploader = () => {
  const [videoData, setVideoData] = useState(null);

  const onDrop = (acceptedFiles) => {
    const file = acceptedFiles[0];
    console.log("file", file);
    const reader = new FileReader();

    reader.onload = () => {
      setVideoData(reader.result); // Videonun içeriğini direkt olarak atıyoruz
      dcc.Store.set('uploaded-video', reader.result); // Base64 kodlama yapmadan direkt atıyoruz
    };

    reader.readAsArrayBuffer(file); // Dosyanın içeriğini array buffer olarak okuyoruz
  };

  const { getRootProps, getInputProps } = useDropzone({
    accept: 'video/mp4,video/quicktime,video/avi', // mp4 ve mov formatlarını kabul ediyoruz
    multiple: false,
    onDrop,
  });

  return (
    <div {...getRootProps()}>
      <input {...getInputProps()} />
      <p>Drag and drop a video file here, or click to select a file</p>
    </div>
  );
};

export default CustomVideoUploader;
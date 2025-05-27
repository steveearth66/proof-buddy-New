export const exportToLocalMachine = (proofName, JSONForm) => {
  // console.log('Exporting to local machine:', JSONForm)
  let fileName = proofName || 'your-JSON-File';
  let blob = new Blob([JSONForm], { type: 'application/json' });
  let href = URL.createObjectURL(blob);
  let link = document.createElement('a');
  link.href = href;
  link.download = fileName + '.json';
  link.click();
};

/**
 * Reads a .txt file and returns the parsed exportData object.
 * @param {File} file - The .txt file to read.
 * @returns {Promise<Object>} - A promise that resolves to the parsed exportData object.
 */
export const readFromFile = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    // Handle file reading
    reader.onload = (event) => {
      try {
        const fileContent = event.target.result;
        const parsedData = JSON.parse(fileContent); // Parse the JSON content
        resolve(parsedData); // Resolve with the parsed data
      } catch (error) {
        reject(new Error("Invalid file format. Please upload a valid .txt file containing JSON."));
      }
    };

    // Handle file reading errors
    reader.onerror = () => {
      reject(new Error("Error reading the file."));
    };

    // Read the file as text
    reader.readAsText(file);
  });
};

const useExportToLocalMachine = (proofName, JSONForm) => {
  /** 
   * Exports the created JSON Object to the user's local machine as a .json file.
   * Runs when the User selects the "JSON" option in the download drop-down menu.
   * - Or will run when the User selects the "Download" option if the drop-down options menu has not yet been implemented.
   * File will be named after the proof name the user entered, if no name is detected, a default name is assigned.
   */
  const exportFormToLocalMachine = () => {
    let fileName = proofName;
    let forToExport = JSONForm; // Should return a JSON Object of the form
    // Create the intended file for download in the browser...
    let blob = new Blob([forToExport], { type: 'application/json' });
    let href = URL.createObjectURL(blob);
    // Creates HTML with the href to a file...
    let link = document.createElement('a');
    link.href = href;

    // Check if user has named their proof, if user has not, will use the default name
    if(fileName == ''){
      // Default Name...
      fileName = 'your-JSON-File';
      link.download = fileName + '.json';
      link.click();
    }
    else{
      // User's Name for their Proof...
      link.download = fileName + '.json';
      link.click();
    }
  };

  return exportFormToLocalMachine;
};

export { useExportToLocalMachine };
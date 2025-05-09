// Custom version that exports the Blank Lines grid and reads a .txt file.

const useExportBlankLinesToLocalMachine = () => {
  /** 
   * Exports the created array of JSON objects to the user's local machine as a .txt file.
   * Runs when the User selects the "JSON" option in the download drop-down menu.
   * File will be named after the proof name the user entered, if no name is detected, a default name is assigned.
   */
  const exportBlankLinesToLocalMachine = (exportData) => {
    try {
      if (!exportData || typeof exportData !== "object") {
        throw new Error("Invalid export data. Please provide a valid object.");
      }

      let fileName = exportData.name || '';
      // Combine metadata and grid data into a single object
      const dataToExport = {
        name: exportData.name || "Unnamed Proof",
        tag: exportData.tag || "",
        lhsGoal: exportData.lhsGoal || "No LHS Goal Specified",
        rhsGoal: exportData.rhsGoal || "No RHS Goal Specified",
        rows: exportData.rows || []
      };

      let forToExport = JSON.stringify(dataToExport, null, 2); // Pretty-print with 2 spaces for readability

      // Create the intended file for download in the browser...
      let blob = new Blob([forToExport], { type: 'text/plain' }); // Export as plain text
      let href = URL.createObjectURL(blob);
      // Creates HTML with the href to a file...
      let link = document.createElement('a');
      link.href = href;

      // Check if user has named their proof, if user has not, will use the default name
      if (fileName === '') {
        fileName = 'your-JSON-File';
      }
      link.download = fileName + '.txt';
      link.click();
    } catch (error) {
      console.error("Error during export:", error.message);
      alert(`Failed to export data: ${error.message}`);
    }
  };

  /**
   * Reads a .txt file and returns the parsed exportData object.
   * @param {File} file - The .txt file to read.
   * @returns {Promise<Object>} - A promise that resolves to the parsed exportData object.
   */
  const readBlankLinesFromFile = (file) => {
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

  return { exportBlankLinesToLocalMachine, readBlankLinesFromFile };
};

export { useExportBlankLinesToLocalMachine };
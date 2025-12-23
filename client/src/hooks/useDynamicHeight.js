import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook to dynamically calculate the available height for scrollable containers
 * that need to account for fixed headers and floating footers
 */
export const useDynamicHeight = (dependencies = []) => {
  const [availableHeight, setAvailableHeight] = useState(0);

  const depsArray = Array.isArray(dependencies) ? dependencies : [dependencies];

  // const calculateHeight = useCallback(() => {
  //   // Get the actual heights of the elements
  //   const header = document.querySelector('header');
  //   const formTopSection = document.querySelector('.form-top-section');
  //   const floatingFooter = document.querySelector('.floating-footer');
  //   
  //   const headerHeight = header ? header.offsetHeight : 68; // fallback to default
  //   const formTopSectionHeight = formTopSection ? formTopSection.offsetHeight : 310; // fallback to default
  //   const floatingFooterHeight = floatingFooter ? floatingFooter.offsetHeight : 120; // fallback to default
  //   
  //   // Calculate available height for the scrollable container
  //   // Add some padding (40px) to provide space between content and footer
  //   const calculated = window.innerHeight - headerHeight - formTopSectionHeight - floatingFooterHeight - 40;
  //   
  //   setAvailableHeight(Math.max(200, calculated)); // Minimum height of 200px
  // }, dependencies); // removed to clean warnings
  const calculateHeight = useCallback(() => {
    // Get the actual heights of the elements
    const header = document.querySelector('header');
    const formTopSection = document.querySelector('.form-top-section');
    const floatingFooter = document.querySelector('.floating-footer');
    
    const headerHeight = header ? header.offsetHeight : 68; // fallback to default
    const formTopSectionHeight = formTopSection ? formTopSection.offsetHeight : 310; // fallback to default
    const floatingFooterHeight = floatingFooter ? floatingFooter.offsetHeight : 120; // fallback to default
    
    // Calculate available height for the scrollable container
    // Add some padding (40px) to provide space between content and footer
    const calculated = window.innerHeight - headerHeight - formTopSectionHeight - floatingFooterHeight - 40;
    
    setAvailableHeight(Math.max(200, calculated)); // Minimum height of 200px
  }, [...depsArray]);

  useEffect(() => {
    // Calculate initial height
    calculateHeight();

    // Recalculate on window resize
    const handleResize = () => {
      calculateHeight();
    };

    // Recalculate when DOM changes (e.g., when form elements load)
    const handleDOMChange = () => {
      setTimeout(calculateHeight, 100); // Small delay to ensure DOM is updated
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);
    
    // Use ResizeObserver to watch for changes in the form top section
    const resizeObserver = new ResizeObserver(handleDOMChange);
    const formTopSection = document.querySelector('.form-top-section');
    if (formTopSection) {
      resizeObserver.observe(formTopSection);
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
      resizeObserver.disconnect();
    };
  }, [calculateHeight]);

  return availableHeight;
};

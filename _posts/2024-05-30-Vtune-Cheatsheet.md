---
layout: post
title: VTune Cheatsheet
date: 2024-05-30
---

# Starting VTune

```
$ cd /opt/intel/oneapi/vtune/latest/bin64
$ ./vtune-gui

# Create a Project

Once the GUI has started, click on the *New Project...* button

# Select a System to Run the Analysis

Click on *Local Host* to run the analysis on the local machine (as opposed to a remote machine).

# Select an Analysis Target

* Select the analysis target. This can be an application or the entire system.
* The application can be a binary or a script.
* Your app may require parameters. Configure them under *application parameters*.

# Performance Snapshot

This gives you a quick overview of potential performance issues. 

* Open the menu to select analysis types.

# Configure Binary and Source Directories

* At the bottom of the GUI, click on the folder icon to select the binary and source directories for post-processing if they do not correspond to debug information.

# Generate a Command Line

* Once you have selected your options you can click on the console icon next to the folder icon to generate a command to run your analysis. This saves you from remembering all of the command line options.

# Start the App and Start to Profile the App

* Click on the start button near the bottom of the GUI to start the application and begin the data collection process.

# Monitor the Elapsed Time

The *elapsed time*, near the top right of the GUI is a great indicator of tuning efforts. Track this before and after making changes.

# Choose your Next Analysis Type

Choose from many analysis types for your next analysis e.g.
* Algorithm
  * Hotspots: Algorithm efficiency
  * Anomaly Detection
  * Memory Consumption
* Parallelism
  * Threading
  * HPC Performance Characterization
* Accelerators
  * GPU Offload
  * GPU Compute/Media Hotspots
  * CPU/FPGA Interaction
* Microarchitecture
  * Microarchitecture Exploration
  * Memory Access
* I/O
  * Input and Output
* Platform Analysis
  * System Overview 
  * GPU Rendering

# Optimizations

* Try to optimize the top hotspot functions
* Click on a function to explore its stack
* Use the CPU Utilization Histogram to analyze the duration that a specific number of CPUs ran simultaneously. 
  * Adjust sliders to set thresholds
* The top right corner is your performance navigator. Use it to plan next steps.

# Calling Sequence

* Use the *Bottom-up* tab to explore each functions calling sequence: from a child up to a parent function.
* Expand a hotspot function to identify a call path with the highest CPU time.
* Group data with available hierarhies e.g. by Module, Thread, HW context...
* Identify all call stacks that called the function selected in the grid.
* Use the Timeline pane to visualize metrics over time at either the thread or platform level
  * Identify patterns, anomalies and trends in the data
  * Select a grouping level for timeline bands e.g. Process, HW context.
  * Drag and drop to select a range on the timeline area.
  * Zoom and/or filter in from the context menu
  * Filter the data in the grid or timeline view.
    * E.g. select ThreadFunction from the Thread menu to filter out other data
* Double click the function to open source and identify code lines that affect performance. Or select *View Source* from the context menu.
* In the Source view, see the code associated with a selection and it's related performance metrics.
* Switch to Assembly view to see disassembled code and related performance metrics.
  * If both views are enabled, source and assembly code selections are synchronized.
* Navigate between code lines that contain the most hostspots.
* Looking for a particular object? Click the magnifier icon to open the *Find* panel.


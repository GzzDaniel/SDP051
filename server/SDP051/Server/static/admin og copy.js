const socket = io("https://sdp051car.com");

let tableData = [];

socket.on("connect", () => {
    console.log("Connected to server"); 
    socket.emit("adminRequestQueue", { message: "ack" });
});


const table = new Tabulator("#my-table", {
    index: "sid",
    data: tableData,
    layout: "fitColumns",
    reactiveData: true,
    resizableColumns: true,
    columns: [
      { title: "session ID", field: "sid", editor: "false" },
      { title: "Time Allowed", field: "timeAllowed", editor: "number" },
      {title: "Time Remaining", field:"timeRemaining", editor: "false"}
    ],

    cellEdited: function(cell){
        let rowData = cell.getRow().getData();
        let rowIdx = cell.getRow().getPosition();

        socket.emit("adminRowUpdate", {rowData, rowIdx});
    }
});
  

socket.on("adminResponseQueue", (queue) => {
    console.log(queue);
    table.replaceData(queue);
});

socket.on("adminResponseRow", (row) => {
    console.log(row);
    table.updateData(row);
});




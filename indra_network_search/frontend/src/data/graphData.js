import {DataSet, Network} from "vis-network/standalone";

export default {
  getNetworkObjWrapper(elementID) {
    const nodes = [
      {id: "CHEBI:1234", label: "Node 1"},
      {id: "CHEBI:4321", label: "Node 2"}
    ];
    const edges = [
      {from: "CHEBI:1234", to: "CHEBI:4321"},
    ];
    return this.getNetworkObj(nodes, edges, elementID);
  },
  getNetworkObj(nodes, edges, elementID) {
    const graphNodes = new DataSet(nodes);
    const graphEdges = new DataSet(edges);
    const graphData = {nodes: graphNodes, edges: graphEdges};
    const graphContainer = document.getElementById(elementID);
    const graphOptions = {};
    return new Network(graphContainer, graphData, graphOptions);
  }
};

<template>
  <div id="vis-js-graph">
  </div>
</template>

<script>
import graphData from "@/data/graphData";

export default {
  methods: {
    loadGraph() {
      const divID = "vis-js-graph";
      return graphData.getNetworkObj(this.nodes, this.edges, divID)
    }
  },
  data() {
    return {
      network: null,
      nodes: [
        {id: "CHEBI:1234", label: "Node 1"},
        {id: "CHEBI:4321", label: "Node 2"}
      ],
      edges: [
        {from: "CHEBI:1234", to: "CHEBI:4321"},
      ],
    }
  },
  mounted() {
    this.network = this.loadGraph()
  }
}
</script>

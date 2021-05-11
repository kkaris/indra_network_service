<template>
  <div class="card text-center">
    <div class="card-header">
      <!-- Header N-edge paths | Source -> {X_n} -> target | source badges | collapse toggle icon -->
      {{ edgeCount }}-edge paths;
      <template v-if="sourceExist"><Node v-bind="source" /></template>
      <template v-else>X0</template>
      <i class="bi bi-arrow-right"></i>
      <template v-for="n in edgeCount - 1" :key="n">
        X{{ n }}<i class="bi bi-arrow-right"></i>
      </template>
      <template v-if="targetExist"><Node v-bind="target" /></template>
      <template v-else>X{{ pathNodeCount + 1 }}</template>
    </div>
    <div class="card-body">
      <!-- Table (or grid) with two columns: Path | Support -->
      <div class="container">
        <table class="table">
          <thead>
          <tr>
            <th scope="col">Path</th>
            <th scope="col">Support</th>
          </tr>
          </thead>
          <tbody>
          <!-- v-for loop over table/grid rows: <Path />; <Path /> currently assumes
               a table encapsulating it -->
            <tr v-for="(path, index) in pathArray" :key="index">
              <Path v-bind="path" />
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
// import Path from "@/components/Result/Path";
import Node from "@/components/Result/Node";
import Path from "@/components/Result/Path";

export default {
  components: {Path, Node},
  props: {
    // Follows one entry in
    // indra_network_search.data_models::PathResultData.paths: Dict[int, List[Path]]
    pathNodeCount: {
      type: Number,
      required: true,
    },
    source: {
      type: Object,
      default: null,
      validator: obj => {
        const notProvided = obj === null;
        const isNode = sharedHelpers.isNode(obj);
        return isNode || notProvided
      }
    },
    target: {
      type: Object,
      default: null,
      validator: obj => {
        const notProvided = obj === null;
        const isNode = sharedHelpers.isNode(obj);
        return isNode || notProvided
      }
    },
    pathArray: {
      type: Array,
      required: true,
      validator: arr => {
        // Check if array and array of Path
        const isArr = Array.isArray(arr);
        // TodO: Find out why 'arr.every(sharedHelpers.isNodeArray)' errors with:
        //  "Uncaught TypeError: arr.every is not a function"
        // console.log('isArr=', isArr);
        // console.log('typeof=', typeof arr);
        // console.log(arr);
        // return isArr && arr.every(sharedHelpers.isNodeArray);
        return isArr;
      }
    }
  },
  created() {
    // Throw error if source && target are null
    if (this.source === null && this.target === null) {
      throw Error('Must provide at least one of source and target as props')
    }
  },
  computed: {
    sourceExist() {
      return this.source !== null
    },
    targetExist() {
      return this.target !== null
    },
    edgeCount() {
      return this.pathNodeCount - 1
    }
  }
}
</script>
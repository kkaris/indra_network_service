<template>
  <div class="container border rounded-lg">
    <h1>Results</h1>
    <p>Click on titles to expand results</p>
    <!--Source/Target info???-->
    <!--Ontology Results-->
    <!--Path Results-->
    <!--Reverse Path Results-->
    <!--Shared Targets-->
    <!--Shared Regulators-->
    <h1>Test Space</h1>
    <div class="container border rounded-lg">
      <p>testNode1: <Node v-bind="testNode1" /></p>
    </div>
    <div class="container border rounded-lg">
      <p>testNode2: <Node v-bind="testNode2" /></p>
    </div>
    <div class="container border rounded-lg">
      <p>Testing StatementTitle:<br/>
        <StatementTitle
          :subj-node="testNode1"
          :obj-node="testNode2"
          :sentence="testStmt111.english"
        />
      </p>
    </div>
<!--    <div class="container border rounded-lg">-->
<!--      <p>Testing StatementData:<br/>-->
<!--        <StatementData-->
<!--        />-->
<!--      </p>-->
<!--    </div>-->
    <div class="container border rounded">
      <p>Testing Edge:<br/>
        <Edge v-bind="testEdge1" />
      </p>
    </div>
    <!-- Test Path -->
    <div class="container border rounded">
      <p>Testing Path:<br/>
        <Path
          :path="testPath"
          :edge_data="testEdgeDataArr"
        />
      </p>
    </div>
    <div class="container border rounded">
      <p>Testing NPathResult</p>
      <p>
        <NPathResult
          :source="testNode1"
          :target="testNode4"
          :path-node-count="testPathDataModel.path.length"
          :path-array="[testPathDataModel, testPathDataModel]"
        />
      </p>
    </div>
  </div>
</template>

<script>
import Node from "@/components/Result/Node";
import StatementTitle from "@/components/Result/StatementTitle";
import Edge from "@/components/Result/Edge";
import Path from "@/components/Result/Path";
import NPathResult from "@/components/Result/NPathResult";

export default {
  components: {NPathResult, Path, Edge, StatementTitle, Node },
  /* To spread together two objects into another object for usage in a v-bind:
  * v-bind="{...this.testStmt111,
  *          subjNode: this.testNode1,
  *          objNode: this.testNode2}"
  * */
  data() {
    return {
      testNode1: {
        name: "BRCA1",
        namespace: "HGNC",
        identifier: "1100",
        sign: 0,
        lookup: "https://identifiers.org/hgnc:1100",
      },
      testNode2: {
        name: "BRCA2",
        namespace: "HGNC",
        identifier: "1101",
        sign: 0,
        lookup: "https://identifiers.org/hgnc:1101",
      },
      testNode3: {
        name: "MEK",
        namespace: "FPLX",
        identifier: "MEK",
        sign: 0,
        lookup: "https://identifiers.org/fplx:MEK",
      },
      testNode4: {
        name: "ERK",
        namespace: "FPLX",
        identifier: "ERK",
        sign: 0,
        lookup: "https://identifiers.org/fplx:ERK",
      },
      testStmt111: {
        stmt_type: "Activation",
        evidence_count: 10,
        stmt_hash: "14631716667987313",
        source_counts: { "reach": 5,
                         "sparser": 5 },
        belief: 0.9991,
        curated: false,
        english: "BRCA1 activates BRCA2",
        weight: null,
        residue: '',
        position: '',
        initial_sign: null,
        db_url_hash:
            "https://db.indra.bio/statements/from_hash/14631716667987313?format=html"
      },
      testStmt112: {
        stmt_type: "Activation",
        evidence_count: 2,
        stmt_hash: "14631716667987315",
        source_counts: { "sparser": 2 },
        belief: 0.9991,
        curated: false,
        english: "BRCA1 activates BRCA2",
        weight: null,
        residue: '',
        position: '',
        initial_sign: null,
        db_url_hash:
            "https://db.indra.bio/statements/from_hash/14631716667987315?format=html"
      },
      testStmt12: {
        stmt_type: "Phosphorylation",
        evidence_count: 2,
        stmt_hash: "94631716667987313",
        source_counts: { "reach": 1,
                         "signor": 1 },
        belief: 0.99992,
        curated: false,
        english: "BRCA1 phosphorylates BRCA2",
        weight: null,
        residue: '',
        position: '',
        initial_sign: null,
        db_url_hash:
            "https://db.indra.bio/statements/from_hash/94631716667987313?format=html"
      },
      testStmt2: {
        stmt_type: "Complex",
        evidence_count: 6,
        stmt_hash: "33742827778098424",
        source_counts: {
          "reach": 2,
          "sparser": 3,
          "Signor": 1
        },
        belief: 0.8991,
        curated: true,
        english: "BRCA2 binds MEK",
        weight: null,
        residue: '',
        position: '',
        initial_sign: null,
        db_url_hash:
            "https://db.indra.bio/statements/from_hash/33742827778098424?format=html"
      },
      testStmt3: {
        stmt_type: "Phosporylation",
        evidence_count: 5,
        stmt_hash: "-33742827778098424",
        source_counts: { "reach": 2,
                         "sparser": 3 },
        belief: 0.8991,
        curated: false,
        english: "MEK Phosphorylates ERK",
        weight: null,
        residue: 'Y',
        position: '204',
        initial_sign: null,
        db_url_hash:
            "https://db.indra.bio/statements/from_hash/-33742827778098424?format=html"
      },
    };
  },
  computed: {
    testEdge1() {
      return {
        edge: [this.testNode1, this.testNode2],
        statements: {
          // Use brackets for using 'this' in object notation
          [this.testStmt111.stmt_type]: [this.testStmt111, this.testStmt112],
          [this.testStmt12.stmt_type]: [this.testStmt12],
        },
        belief: 0.99,
        weight: 1.5,
        sign: null,
        context_weight: 'N/A',
        db_url_edge: 'unset'
      }
    },
    testEdge2() {
      return {
        edge: [this.testNode2, this.testNode3],
        statements: { [this.testStmt2.stmt_type]: [this.testStmt2] },
        belief: 0.98,
        weight: 1.2,
        sign: null,
        context_weight: 'N/A',
        db_url_edge: 'unset'
      }
    },
    testEdge3() {
      return {
        edge: [this.testNode3, this.testNode4],
        statements: { [this.testStmt3.stmt_type]: [this.testStmt3] },
        belief: 0.8,
        weight: 1.1,
        sign: null,
        context_weight: 'N/A',
        db_url_edge: 'unset'
      }
    },
    testPath() {
      return [this.testNode1, this.testNode2, this.testNode3, this.testNode4]
    },
    testEdgeDataArr() {
      return [this.testEdge1, this.testEdge2, this.testEdge3]
    },
    testPathDataModel() {
      // indra_network_search.data_models::Path
      return {
        path: this.testPath,
        edge_data: this.testEdgeDataArr
      }
    },
    testNPathRes() {
      // indra_network_search.data_models::PathResultData.paths
      const nodeCount = this.testPathDataModel.path.length;
      return {[nodeCount]: [this.testPathDataModel, this.testPathDataModel]}
    },
    testPathResultData() {
      // indra_network_search.data_models::PathResultData
      return {
        source: this.testNode1,
        target: this.testNode4,
        paths: this.testNPathRes
      }
    }
  },
};
</script>

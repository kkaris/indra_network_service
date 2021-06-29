<template>
  <div class="card text-center">
    <div class="card-header">
      <div class="d-flex justify-content-between">
        <h2>Common Parents</h2>
        <a
            role="button"
            data-bs-toggle="collapse"
            :href="`#${strUUID}`"
            :aria-expanded="false"
            :aria-controls="strUUID"
        >
          <i title="Click to expand" class="bi-plus-circle fs-2"></i>
        </a>
      </div>
    </div>
    <div class="card-body collapse show" :id="strUUID">
      <div class="container">
        <table class="table table-borderless table-hover">
          <thead>
            <tr>
              <th>Name</th>
              <th>Namespace</th>
              <th>Identifier</th>
              <th>Lookup</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(pnode, key, index) in parents" :key="index">
              <tr>
                <td><NodeModal v-bind="pnode"/></td>
                <td>{{ pnode.namespace }}</td>
                <td>{{ pnode.identifier }}</td>
                <td class="col">
                  <a :href="pnode.lookup"><i class="bi bi-box-arrow-up-right"></i></a>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import sharedHelpers from "@/helpers/sharedHelpers";
import UniqueID from "@/helpers/BasicHelpers";
import NodeModal from "@/components/Result/NodeModal";

export default {
  components: {NodeModal},
  props: {
    source: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isNode(obj)
      }
    },
    target: {
      type: Object,
      required: true,
      validator: obj => {
        return sharedHelpers.isNode(obj)
      }
    },
    parents: {
      type: Array,
      required: true,
      validator: arr => {
        const isNotEmpty = arr.length > 0;
        const isNodeArray = sharedHelpers.isNodeArray(arr);

        return isNotEmpty && isNodeArray
      }
    }
  },
  setup() {
    const uuid = UniqueID().getID();
    return {
      uuid,
    }
  },
  computed: {
    strUUID() {
      return `collapse-${this.uuid}`
    },
  },
}
</script>

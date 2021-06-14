// noinspection OverlyComplexBooleanExpressionJS

const isEmptyObject = function (obj) {
  for (let i in obj) {
    if (i) {
      return false;
    }
  }
  return true;
};

const isNode = function (obj) {
  return obj.name && obj.identifier && obj.namespace;
};

const isStr = function (str) {
  return typeof str === 'string';
};

export default {
  isEmptyObject,
  isNode,
  isStr,
  isOptionalNode(obj) {
    const notProvided = Boolean(obj);
    const isNodeObj = isNode(obj);
    return isNodeObj || notProvided;
  },
  isSourceCount(obj) {
    // Empty objects are not allowed
    if (this.isEmptyObject(obj)) {
      return false;
    }

    // Test if key is str and value is integer/number
    for (const [key, value] of Object.entries(obj)) {
      const isStr = this.isStr(key);
      const isNum = typeof value === 'number';
      const geqZero = value >= 0;
      if (!(isStr && isNum && geqZero)) {
        return false;
      }
    }
    return true;
  },
  isStmtData(obj) {
    // Using Boolean for the simple properties that are expected to have a
    // value that does not evaluate to False
    const st = Boolean(obj.stmt_type); // String !== ''
    const ec = Boolean(obj.evidence_count); // Number > 0
    const sh = Boolean(obj.stmt_hash); //
    const sco = typeof obj.source_counts === 'object';
    const scn = !(isEmptyObject(obj.source_counts));
    const sc = sco && scn;
    const bl = typeof obj.belief === 'number';
    const cr = typeof obj.curated === 'boolean';
    const en = Boolean(obj.english);
    const ur = Boolean(obj.db_url_hash);

    return st && ec && sh && sc && bl && cr && en && ur;
  },
  isNodeArray(arr) {
      const notEmpty = arr.length > 0;
      const containsNodes = arr.every(isNode);

    return notEmpty && containsNodes;
  },
  isStmtDataArray(arr) {
    const notEmpty = arr.length > 0;
    const containsStmtData = arr.every(this.isStmtData);
    return notEmpty && containsStmtData;
  },
  isStmtTypeSupport(obj) {
    const stIsStr = this.isStr(obj.stmt_type); // str
    const stStr = Boolean(obj.stmt_type); // str
    const srcCount = this.isSourceCount(obj.source_counts);
    const isStmtArr = typeof obj.statements === 'object' &&
      this.isStmtDataArray(obj.statements); // List[StmtData]

    return stIsStr && stStr && srcCount && isStmtArr;
  },
  mergeSourceCounts(srcObjArr) {
    // Source: https://dev.to/ramonak/javascript-how-to-merge-multiple-objects-with-sum-of-values-43fd
    // An array of source counts [{sparser: 5, isi: 1}, {sparser: 2}]
    const result = srcObjArr.reduce((srcObj, src) => {
      for (const [source, count] of Object.entries(src)) {
        if (!srcObj[source]) {
          srcObj[source] = 0;
        }
        srcObj[source] += count;
      }
      return srcObj;
      }, {});
    return result;
  },
  getSourceCounts(stmtDataArr) {
    // Array of stmtData -> array of source counts
    let srcObjArray = [];
    for (let stmtDataObj of stmtDataArr) {
      srcObjArray.push(stmtDataObj.source_counts);
    }
    return this.mergeSourceCounts(srcObjArray);
  }
};

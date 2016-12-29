module.exports = function(fileInfo, api) {
  var mountPoint = process.env.ELM_DOC_MOUNT_POINT;

  if (typeof mountPoint === 'undefined') {
    return;
  }

  var j = api.jscodeshift;

  function prependMountpointToStringLiteral(path) {
    var value = path.node.value;
    if (typeof value === 'string') {
      if (/^(\/packages|\/all-packages|\/new-packages|\/assets\/)/.test(value)) {
        return j.literal(mountPoint + value);
      }
    }
    return path.node;
  }

  function prependMountpointToHref(path) {
    var node = path.node;
    if (node.arguments.length === 1 &&
        node.arguments[0].type === 'Literal' &&
        node.arguments[0].value === '/') {
      return j.callExpression(
        j.identifier(node.callee.name),
        [j.literal(mountPoint + '/')]
      );
    }
    return path.node;
  }

  var root = j(fileInfo.source);
  root
    .find(j.Literal)
    .replaceWith(prependMountpointToStringLiteral);
  root
    .find(j.CallExpression, {
      callee: {name: '_elm_lang$html$Html_Attributes$href'}
    })
    .replaceWith(prependMountpointToHref);
  return root.toSource();
}

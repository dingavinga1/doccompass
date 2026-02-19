import { useState } from "react";

import type { DocumentationTreeNode } from "../api/types";

interface SectionTreeProps {
  roots: DocumentationTreeNode[];
  selectedPath?: string;
  onSelect: (path: string) => void;
}

interface TreeNodeProps {
  node: DocumentationTreeNode;
  selectedPath?: string;
  onSelect: (path: string) => void;
  defaultExpanded?: boolean;
}

function TreeNode({ node, selectedPath, onSelect, defaultExpanded = false }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const isSelected = selectedPath === node.path;
  const hasChildren = node.children.length > 0;

  function handleToggle(event: React.MouseEvent) {
    event.stopPropagation();
    setExpanded((prev) => !prev);
  }

  return (
    <li>
      <div className="tree-node-header">
        <button
          type="button"
          className={`tree-toggle${hasChildren ? "" : " leaf"}`}
          onClick={handleToggle}
          aria-label={expanded ? "Collapse" : "Expand"}
        >
          {hasChildren ? (expanded ? "▾" : "▸") : "·"}
        </button>
        <button
          type="button"
          className={`tree-node-btn${isSelected ? " selected" : ""}`}
          onClick={() => {
            onSelect(node.path);
            if (hasChildren && !expanded) {
              setExpanded(true);
            }
          }}
          title={node.path}
        >
          {node.title ?? node.path}
        </button>
      </div>
      {hasChildren && expanded ? (
        <ul>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              selectedPath={selectedPath}
              onSelect={onSelect}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function SectionTree({ roots, selectedPath, onSelect }: SectionTreeProps) {
  if (!roots.length) {
    return <p className="empty-state">No sections available.</p>;
  }

  return (
    <div className="section-tree-container">
      <ul className="section-tree" aria-label="Documentation section tree">
        {roots.map((root) => (
          <TreeNode
            key={root.id}
            node={root}
            selectedPath={selectedPath}
            onSelect={onSelect}
            defaultExpanded
          />
        ))}
      </ul>
    </div>
  );
}

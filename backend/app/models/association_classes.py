"""Preserve association-class notation in the editor; lower it only for codegen."""
from copy import deepcopy
from .uml_model import UMLRelationship, RelationshipEnd, RelationshipType


def normalize_association_classes(diagram):
    if not any(r.association_class_id for r in diagram.relationships):
        return diagram
    result = deepcopy(diagram)
    classes = {c.id: c for c in result.classes}
    used, relationships = set(), []
    for rel in result.relationships:
        ref = rel.association_class_id
        if not ref:
            relationships.append(rel)
            continue
        if ref not in classes:
            raise ValueError('La clase de asociación no existe en el diagrama.')
        if classes[ref].is_interface or classes[ref].is_abstract:
            raise ValueError('La clase de asociación debe ser una clase concreta.')
        if rel.type != RelationshipType.ASSOCIATION:
            raise ValueError('Una clase de asociación solo puede vincularse a una asociación.')
        if ref in (rel.source.class_id, rel.target.class_id) or rel.source.class_id == rel.target.class_id:
            raise ValueError('La clase de asociación debe ser distinta de los dos extremos.')
        if ref in used:
            raise ValueError('Una clase de asociación no puede representar dos asociaciones distintas.')
        used.add(ref)
        if any(end.multiplicity not in ('*', '0..*', '1..*') for end in (rel.source, rel.target)):
            raise ValueError('Esta implementación de clase de asociación requiere muchos a muchos (*, 0..* o 1..*) en ambos extremos.')
        # A link instance belongs to exactly one instance of each endpoint.
        # The opposite endpoint's bounds become the number of link instances.
        for suffix, parent, count in (
            ('source', rel.source, rel.target.multiplicity),
            ('target', rel.target, rel.source.multiplicity),
        ):
            relationships.append(UMLRelationship(
                id=f'{rel.id}-{suffix}', type=RelationshipType.ASSOCIATION,
                source=RelationshipEnd(class_id=parent.class_id, multiplicity='1', navigable=False),
                target=RelationshipEnd(class_id=ref, multiplicity=count, navigable=False),
            ))
    result.relationships = relationships
    return result

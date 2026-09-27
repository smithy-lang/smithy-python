$version: "2.0"
metadata suppressions = [{id: "Foo", namespace: "example.mini"}]
metadata zeta = "last"
metadata alpha = 1
namespace example.mini

@paginated(inputToken: "nextToken", outputToken: "nextToken")
service Mini {
    version: "2024-01-01"
    operations: [GetThing]
    resources: [Widget]
    errors: [ServiceError]
    rename: { "example.mini#Nested": "RenamedNested" }
}

resource Widget {
    identifiers: { widgetId: String }
    properties: { name: String }
    read: GetWidget
    list: ListWidgets
    operations: [PokeWidget]
    collectionOperations: [BatchPoke]
}

@readonly
operation GetWidget { input := @references([{resource: Widget}]) { @required widgetId: String } output := { name: String } }
@readonly @paginated(items: "items")
operation ListWidgets { input := { nextToken: String } output := { nextToken: String, items: StringList } }
operation PokeWidget { input := { @required widgetId: String } output := {} }
operation BatchPoke { input := {} output := {} }
@error("server") structure ServiceError { message: String }

@mixin
structure IdMixin {
    /// The id.
    @required
    id: String
    tag: String
}

@mixin(localTraits: [internal])
@internal
structure StampMixin with [IdMixin] {
    created: Timestamp
}

structure Thing with [StampMixin] {
    zzz: Integer
    aaa: Nested
    unionish: Choice
    things: ThingList
    lookup: ThingMap
    color: Color
    level: Level
    doc: Document
    @default(0)
    prim: PrimitiveInteger
    @default(5)
    defaulted: Integer
}

apply Thing$id @documentation("Overridden doc.")
apply Thing$tag @length(min: 1)

structure Nested { b: String, a: String }
union Choice { text: String, count: Integer }
list ThingList { member: Thing }
list StringList { member: String }
@sparse map ThingMap { key: String, value: Nested }
enum Color {
    RED = "red"
    GREEN
    BLUE = "blue"
}
intEnum Level {
    LOW = 1
    HIGH = 10
}

operation GetThing { input := { id: String } output := { thing: Thing } errors: [ServiceError] }

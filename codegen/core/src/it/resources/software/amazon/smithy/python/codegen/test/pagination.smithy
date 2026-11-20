$version: "2.0"

namespace example.pages

use aws.protocols#restJson1

// The service's trait supplies each setting an operation's own trait omits. Only
// operations with their own trait are paginated.
//
// The clients, Paginator and AsyncPaginator, are named like the runtime types
// their paginators of pages return.
@restJson1
@paginated(inputToken: "nextToken", outputToken: "nextToken", pageSize: "maxResults")
service Paginator {
    version: "2026-11-19"
    operations: [
        ListThings
        ScanItems
        Count
        Inspect
        Ordinary
        Foo
        PaginateFoo
        Close
        Upload
    ]
    resources: [
        Shelf
    ]
}

// A resource's operations are the service's too.
resource Shelf {
    operations: [
        ListBooks
    ]
}

// Inherits every token setting and adds items.
@paginated(items: "things")
@http(method: "POST", uri: "/things")
operation ListThings {
    input := {
        nextToken: String
        maxResults: Integer
    }
    output := {
        nextToken: String
        things: Things
    }
}

// Overrides the input token and both paths, and inherits the page size. The input
// token's Python name is escaped past its sibling's, and the items path ends at a
// member whose Python name is escaped.
@paginated(inputToken: "plugins", outputToken: "page.nextToken", items: "page.class")
@http(method: "POST", uri: "/scan")
operation ScanItems {
    input := {
        plugins: String
        plugins_: String
        maxResults: Integer
    }
    output := {
        page: ScanPage
    }
}

// No items, so its paginator has no items().
@paginated
@http(method: "POST", uri: "/count")
operation Count {
    input := {
        nextToken: String
        maxResults: Integer
    }
    output := {
        nextToken: String
        total: Integer
    }
}

// Its items are lists, in a sparse list.
@paginated(items: "rows")
@http(method: "POST", uri: "/inspect")
operation Inspect {
    input := {
        nextToken: String
        maxResults: Integer
    }
    output := {
        nextToken: String
        rows: Rows
    }
}

// Has the members but not the trait, so it is not paginated.
@http(method: "POST", uri: "/ordinary")
operation Ordinary {
    input := {
        nextToken: String
        maxResults: Integer
    }
    output := {
        nextToken: String
    }
}

// Its paginator's name, paginate_foo, is PaginateFoo's method.
@paginated
@http(method: "POST", uri: "/foo")
operation Foo {
    input := {
        nextToken: String
        maxResults: Integer
    }
    output := {
        nextToken: String
    }
}

@paginated
@http(method: "POST", uri: "/paginate-foo")
operation PaginateFoo {
    input := {
        nextToken: String
        maxResults: Integer
    }
    output := {
        nextToken: String
    }
}

// Its method is close_, since clients have a close method.
@paginated
@http(method: "POST", uri: "/close")
operation Close {
    input := {
        nextToken: String
        maxResults: Integer
    }
    output := {
        nextToken: String
    }
}

// Its streaming input can't be sent again for each page, so it has no paginator.
@paginated
@http(method: "POST", uri: "/upload")
operation Upload {
    input := {
        @httpHeader("x-next-token")
        nextToken: String

        @httpHeader("x-max-results")
        maxResults: Integer

        @httpPayload
        @required
        body: Body
    }
    output := {
        nextToken: String
    }
}

@streaming
blob Body

// Overrides only the output token. Its items are a list of a string alias.
@readonly
@paginated(outputToken: "nextPage", items: "titles")
@http(method: "GET", uri: "/books")
operation ListBooks {
    input := {
        @httpQuery("nextToken")
        nextToken: String

        @httpQuery("maxResults")
        maxResults: Integer
    }
    output := {
        nextPage: String
        titles: Titles
    }
}

structure Thing {
    name: String
}

list Things {
    member: Thing
}

structure ScanPage {
    nextToken: String
    class: Entries
}

@sparse
map Entries {
    key: String
    value: Plugin
}

// Named like the plugin type every client method takes.
structure Plugin {
    name: String
}

@sparse
list Rows {
    member: Row
}

list Row {
    member: AsyncItemPaginator
}

// Named like the runtime type the async client returns for Inspect.
structure AsyncItemPaginator {
    name: String
}

list Titles {
    member: Title
}

string Title

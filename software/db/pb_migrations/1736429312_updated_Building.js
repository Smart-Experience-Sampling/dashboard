/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_1482120091")

  // update collection data
  unmarshal({
    "name": "building"
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_1482120091")

  // update collection data
  unmarshal({
    "name": "Building"
  }, collection)

  return app.save(collection)
})

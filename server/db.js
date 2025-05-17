import { MongoClient, ServerApiVersion } from 'mongodb';

const uri = "mongodb+srv://shendeprajyot:Prajyot%401011@cluster0.c9085tk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0";

const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  }
});

export async function connectDB() {
  try {
    await client.connect();
    console.log("Connected to MongoDB!");
    return client.db("Cluster0");
  } catch (err) {
    console.error("MongoDB connection error:", err);
    throw err;
  }
}

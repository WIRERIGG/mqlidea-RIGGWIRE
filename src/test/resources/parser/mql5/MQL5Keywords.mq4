// Test file for MQL5-specific keyword parsing
// This file tests override, final, abstract, sinput keywords

--- VALID ---

sinput int OptimizationParam = 10;

abstract class CBase
{
public:
   virtual void DoWork() = 0;
   virtual int Calculate() const = 0;
};

class CDerived final : public CBase
{
private:
   int m_value;
public:
   CDerived() : m_value(0) {}
   ~CDerived() {}

   void DoWork() override
   {
   }

   int Calculate() const override final
   {
      return m_value;
   }
};

interface ISerializable
{
   bool Save(int fileHandle);
   bool Load(int fileHandle);
};

class CData : public CDerived, public ISerializable
{
public:
   bool Save(int fileHandle) override { return true; }
   bool Load(int fileHandle) override { return true; }
};

void ProcessStrategy(const CBase &strategy)
{
}

template<typename T>
T MaxValue(T a, T b)
{
   if(a > b) return a;
   return b;
}
